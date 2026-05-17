// Recursive Fibonacci. Exercises recursion, if/else, comparisons.
// Expected: REA = 55 when main halts (fib(10)).

int fib(int n) {
    if (n < 2) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int main(void) {
    return fib(10);
}
