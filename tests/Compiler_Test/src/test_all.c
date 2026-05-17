// Combined driver for the cc.py example suite.
// All four tests live in one translation unit so they share a single .CCode
// segment (cc.py emits one .CCode per file, and the linker overlays segments
// of the same name across objects — so splitting them across files would
// collide at link time).
//
// After HALT:
//   REA      = 145              (sum of all four results)
//   r_add    = 7
//   r_fib    = 55
//   r_lsum   = 55
//   r_array  = 28
//
// Inspect r_* in .CData memory (mem.cfg places it at 0x008000) to see each
// test's individual result.

int r_add;
int r_fib;
int r_lsum;
int r_array;

int add(int a, int b) {
    return a + b;
}

int fib(int n) {
    if (n < 2) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int loop_sum(int n) {
    int total;
    int i;
    total = 0;
    i = 1;
    while (i <= n) {
        total = total + i;
        i = i + 1;
    }
    return total;
}

int array_test(void) {
    int a[7];
    int i;
    int total;

    i = 0;
    while (i < 7) {
        a[i] = i + 1;
        i = i + 1;
    }

    total = 0;
    i = 0;
    while (i < 7) {
        total = total + a[i];
        i = i + 1;
    }

    return total;
}

int main(void) {
    r_add   = add(3, 4);
    r_fib   = fib(10);
    r_lsum  = loop_sum(10);
    r_array = array_test();
    return r_add + r_fib + r_lsum + r_array;
}
