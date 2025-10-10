import re
import sys
import json
import os
from typing import Dict, List, Tuple

class MemoryConfig:
    """Parses and stores memory configuration."""
    def __init__(self, config_file: str):
        self.segments: Dict[str, Tuple[int, int]] = {}  # segment_name -> (start, size)
        self._parse_config(config_file)
    
    def _parse_config(self, config_file: str):
        with open(config_file, 'r') as f:
            for line in f:
                # Skip comments and empty lines
                if ';' in line:
                    line = line[:line.find(';')]
                line = line.strip()
                if not line:
                    continue
                
                # Parse segment: .SegmentName : Start = 0xADDR, Size = 0xSIZE
                match = re.match(r'\.(\w+)\s*:\s*Start\s*=\s*(0x[0-9a-fA-F]+|[0-9]+)\s*,\s*Size\s*=\s*(0x[0-9a-fA-F]+|[0-9]+)', line, re.IGNORECASE)
                if match:
                    segment_name = match.group(1).upper()
                    start_addr = int(match.group(2), 0)
                    size = int(match.group(3), 0)
                    self.segments[segment_name] = (start_addr, size)
                else:
                    raise SyntaxError(f"Invalid memory config line: {line}")
    
    def get_segment_address(self, segment_name: str) -> int:
        if segment_name not in self.segments:
            raise ValueError(f"Segment '{segment_name}' not defined in memory config")
        return self.segments[segment_name][0]
    
    def get_segment_size(self, segment_name: str) -> int:
        if segment_name not in self.segments:
            raise ValueError(f"Segment '{segment_name}' not defined in memory config")
        return self.segments[segment_name][1]


class RelocatableObject:
    """Represents a compiled object file."""
    def __init__(self, filename: str):
        self.filename = filename
        self.segments: Dict[str, List[int]] = {}
        self.labels: Dict[str, Tuple[str, int]] = {}
        self.relocations: List[Dict] = []
        self.imports: List[str] = []
    
    @staticmethod
    def from_dict(data: dict) -> 'RelocatableObject':
        obj = RelocatableObject(data['filename'])
        obj.segments = data['segments']
        obj.labels = data['labels']
        obj.relocations = data['relocations']
        obj.imports = data['imports']
        return obj


class Linker:
    """Links multiple object files into a final memory image."""
    def __init__(self, mem_config: MemoryConfig, source_dir: str = '.'):
        self.mem_config = mem_config
        self.source_dir = source_dir
        self.loaded_objects: Dict[str, RelocatableObject] = {}
        self.global_labels: Dict[str, int] = {}
        self.memory_image: Dict[int, int] = {}  # Changed to dictionary for sparse storage
    
    def load_object(self, obj_file: str, namespace: str = None, parent_namespace: str = None) -> RelocatableObject:
        """Load an object file and assign it a namespace."""
        # Normalize path for lookup
        normalized_path = os.path.normpath(obj_file)
        
        if (normalized_path in self.loaded_objects):
            return self.loaded_objects[normalized_path]
        
        with open(obj_file, 'r') as f:
            data = json.load(f)
        
        obj = RelocatableObject.from_dict(data)
        
        # Determine namespace
        if namespace is None:
            base_filename = os.path.basename(obj_file)
            namespace = base_filename.replace('.obj', '').replace('.asm', '').upper()
        else:
            namespace = namespace.upper()
        
        # Recursively load imports
        for import_file in obj.imports:
            # Check if it's a .asm file and convert to .obj
            import_obj_file = import_file.replace('.asm', '.obj')
            import_path = os.path.join(self.source_dir, import_obj_file)
            
            # Import files don't get a namespace override unless explicitly specified
            import_base = os.path.basename(import_file).replace('.asm', '').replace('.obj', '').upper()
            self.load_object(import_path, import_base, namespace)
        
        # Register labels with namespace
        for label_name, (segment, offset) in obj.labels.items():
            # Calculate absolute address
            segment_base = self.mem_config.get_segment_address(segment)
            absolute_addr = segment_base + offset
            
            # Register with namespace
            qualified_name = f"{namespace}.{label_name}"
            self.global_labels[qualified_name] = absolute_addr
            
            # Also register without namespace for local references within same file
            self.global_labels[label_name] = absolute_addr
        
        self.loaded_objects[normalized_path] = obj
        return obj
    
    def link(self, main_obj_file: str) -> Dict[int, int]:
        print(f"Loading main object file: {main_obj_file}")
        main_obj = self.load_object(main_obj_file)
        
        # Fixed size for 24-bit addressing (2^24 cells)
        MEMORY_SIZE = 1 << 24
        print(f"Initializing sparse memory image (max {MEMORY_SIZE:,} words)...")
        self.memory_image = {}  # Only store non-zero values
        
        # Place all segments from all loaded objects
        for obj_file, obj in self.loaded_objects.items():
            for segment_name, bytecode in obj.segments.items():
                segment_base = self.mem_config.get_segment_address(segment_name)
                segment_size = self.mem_config.get_segment_size(segment_name)
                
                # Check if segment fits
                if len(bytecode) > segment_size:
                    raise MemoryError(f"Segment '{segment_name}' in '{obj_file}' exceeds configured size")
                
                # Check if segment is within memory bounds
                if segment_base + len(bytecode) > MEMORY_SIZE:
                    raise MemoryError(f"Segment '{segment_name}' in '{obj_file}' exceeds memory bounds")
                
                # Copy bytecode to memory image
                for i, word in enumerate(bytecode):
                    if word != 0:  # Only store non-zero values
                        self.memory_image[segment_base + i] = word
        
        # Resolve all relocations
        for obj_file, obj in self.loaded_objects.items():
            for reloc in obj.relocations:
                segment = reloc['segment']
                offset = reloc['offset']
                symbol = reloc['symbol']
                
                # Calculate absolute position in memory
                segment_base = self.mem_config.get_segment_address(segment)
                abs_position = segment_base + offset
                
                # Resolve symbol
                if symbol not in self.global_labels:
                    raise ValueError(f"Undefined symbol: {symbol}")
                
                target_address = self.global_labels[symbol]
                
                # Patch memory image
                self.memory_image[abs_position] = target_address
        
        return self.memory_image
    
    def write_output(self, output_file: str):
        """Write memory image to output file in Logisim format."""
        print("Writing output file...")
        file_content = "v2.0 raw\n"
        
        MEMORY_SIZE = 1 << 24  # 16,777,216 words
        WORDS_PER_LINE = 4
        CHUNK_SIZE = 1024  # Write in chunks to manage memory
        
        with open(output_file, 'w') as f:
            f.write(file_content)
            
            # Write complete memory image in chunks of 4 words per line
            for addr in range(0, MEMORY_SIZE, WORDS_PER_LINE):
                # Get 4 words (or zeros if not present)
                row = [self.memory_image.get(addr + i, 0) for i in range(WORDS_PER_LINE)]
                line = ' '.join(f"{word:06X}" for word in row) + "\n"
                f.write(line)
                
                # Show progress every 1M words
                if addr % (1 << 20) == 0:
                    print(f"Writing... {addr >> 20}MB / 16MB")
        
        print("Done writing memory image")


def main(main_obj_file, mem_config_file, output_file):
    # Load memory configuration
    try:
        mem_config = MemoryConfig(mem_config_file)
    except Exception as e:
        print(f"Error loading memory config: {e}")
        sys.exit(1)
    
    # Create linker
    linker = Linker(mem_config)
    
    # Link
    try:
        memory_image = linker.link(main_obj_file)
    except Exception as e:
        print(f"Linking failed: {e}")
        print(f"\nAvailable symbols:")
        for symbol, addr in sorted(linker.global_labels.items()):
            print(f"  {symbol}: 0x{addr:06X}")
        sys.exit(1)
    
    # Write output
    linker.write_output(output_file)
    
    print(f"Linked image generated: {output_file}")
    print(f"Memory image size: {len(memory_image)} words ({len(memory_image) * 3} bytes)")
    print(f"Segments placed:")
    for segment_name, (start, size) in mem_config.segments.items():
        print(f"  {segment_name}: 0x{start:06X} - 0x{start+size-1:06X} ({size} words)")
    print(f"\nResolved labels: {len(linker.global_labels)}")
    for symbol, addr in sorted(linker.global_labels.items()):
        print(f"  {symbol}: 0x{addr:06X}")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python linker.py <main.obj> <mem.cfg> <output.o>")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2], sys.argv[3])