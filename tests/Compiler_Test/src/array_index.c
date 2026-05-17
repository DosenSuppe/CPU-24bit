// Local array, indexing, pointers. Fills then sums.
// Expected: REA = 28 when main halts (1+2+3+4+5+6+7 = 28).

int main(void) {
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
