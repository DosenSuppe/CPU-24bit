# The Linker
The linker is responsible for combining one or more object files produced by the compiler into a single binary image that can be loaded into the CPU simulation. While the compiler translates source code into intermediate object files (.obj), the linker resolves memory placement, applies the configuration defined in memory.cfg, and generates the final output file (.o).

This step is essential because the CPU requires a complete memory image with correctly mapped segments before execution. The linker ensures that all code and data are placed in the right locations, producing a binary that can be directly loaded into Logisim or other simulation environments.

## Using The Linker

For Windows:
<pre>
py .\DevTools\Linker.py &lt;entry_file.obj&gt; &lt;memory.cfg&gt; &lt;output.o&gt;
</pre>
- Entry object: The starting object file produced by the compiler (e.g., main.obj).
- Memory config: A configuration file (memory.cfg) that defines segment mapping and absolute placement.
- Output image: The resulting full RAM image (output.o). If no explicit path is provided, it is written to the current working directory.

The linker builds the complete memory image based on memory.cfg and emits a single binary file suitable for loading into Logisim.

## Examples
### Default output in current directory
<pre>
py .\DevTools\Linker.py .\build\main.obj .\config\memory.cfg output.o
</pre>

### Explicit output path
<pre>
py .\DevTools\Linker.py .\build\main.obj .\config\memory.cfg .\dist\ram_image.o
</pre>