// Smallest interesting program: pass two args, return their sum.
// Expected: REA = 7 when main halts.

int add(int a, int b) {
    return a + b;
}

int main(void) {
    int x;
    int y;
    x = 3;
    y = 4;
    return add(x, y);
}

