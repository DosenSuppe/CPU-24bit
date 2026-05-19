// Bump allocator for the CPU-24bit C runtime.
//
// Hands out memory from $Heap.Start (set in mem.cfg) and advances a
// pointer. Never reclaims memory — `free()` is a no-op so user code can
// call it without #ifdef'ing the call site. Adequate for static
// allocation patterns and for getting linked lists / trees off the
// ground.
//
// Build as a library: `cc.py heap.c --no-entry`. Link alongside any
// program that calls malloc/free, plus `_heap_start.obj` which provides
// the linker-symbol stub.

// Returns the address of $Heap.Start. Implemented in _heap_start.asm
// (cc.py has no syntax for referencing memory-config symbols directly).
extern int *_heap_start(void);

// Internal allocator state — module-local in spirit. Cleared to zero by
// the .CData segment's default initialization, so `heap_initialized == 0`
// on first call.
int *heap_top;
int  heap_initialized;

int *malloc(int n_words) {
    int *result;
    if (heap_initialized == 0) {
        heap_top = _heap_start();
        heap_initialized = 1;
    }
    result = heap_top;
    heap_top = heap_top + n_words;
    return result;
}

void free(int *p) {
    // No-op. A bump allocator can't reclaim individual allocations;
    // memory lives until program halt. Defined so user code can match
    // the malloc/free API without conditional compilation.
}
