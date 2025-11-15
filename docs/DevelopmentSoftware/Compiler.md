# The Compiler
As part of revisiting the 16‑bit CPU project, I also decided to create a compiler to make it easier to test the CPU and write programs for it.

In its current form, the compiler is fairly bulky and definitely in need of cleanup. However, it is functional and serves its purpose for now.

## Using The Compiler

For Windows:
<pre>
py .\DevTools\Compiler.py &lt;input-file&gt;
</pre>
- If the selected file is located within a `src` folder, the compiler will create a `bin` folder alongside it and place the output file there, preserving the directory structure.

- If the selected file is not within a `src` folder, the generated .obj file will be placed in the current root directory.

The compiler does not immediately produce a binary file. Instead, it generates an intermediate object file that is later used in the linking process. The final binary, which can be loaded into Logisim, is created by the [Linker](./Linker.md).