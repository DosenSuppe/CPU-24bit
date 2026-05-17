// Demonstrates syscall builtin and inline asm.
// Assumes the OS provides a TTY-write syscall numbered 1 that reads the
// character from REB. Adjust the number once the OS syscall dispatcher exists.
//
// Also shows inline assembly for direct memory-mapped TTY writes, useful
// before the syscall dispatcher is in place.

int main(void) {
    // Option A: via syscall (requires OS-side dispatcher)
    syscall(1, 'H');
    syscall(1, 'i');
    syscall(1, '\n');

    // Option B: direct write via inline asm (MemDevice1 = 0x900000)
    asm("LDI REA, #0x48");       // 'H'
    asm("LDI REZ, #0x900002");
    asm("STR REZ, REA");

    return 0;
}
