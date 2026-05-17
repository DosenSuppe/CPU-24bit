// For-loop accumulation: sum(n) = 1+2+...+n.
// Expected: REA = 55 when main halts (sum(10)).

int sum(int n) {
    int total;
    total = 0;
    for (int i = 1; i <= n; i = i + 1) {
        total = total + i;
    }
    return total;
}

int main(void) {
    // Also exercise empty-init / empty-update forms.
    int acc;
    acc = 0;
    int j;
    for (j = 0; j < 3; ) {
        acc = acc + 1;
        j = j + 1;
    }
    return sum(10) + acc - 3;  // 55 + 3 - 3 = 55
}
