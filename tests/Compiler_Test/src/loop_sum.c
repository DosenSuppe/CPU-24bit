// While-loop accumulation: sum(n) = 1+2+...+n.
// Expected: REA = 55 when main halts (sum(10)).

int sum(int n) {
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

int main(void) {
    return sum(10);
}
