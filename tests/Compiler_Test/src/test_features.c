// Exercises the v1.1 language additions: #include, const, ternary,
// ++/--, break/continue, and string-literal array init.

#include "common.h"
#include "common.h"  // second include should be skipped by #pragma once

int test_inc_dec(void) {
    int x = 5;
    int a = x++;    // a = 5, x = 6
    int b = ++x;    // x = 7, b = 7
    int c = x--;    // c = 7, x = 6
    int d = --x;    // x = 5, d = 5
    return a + b + c + d;  // 5 + 7 + 7 + 5 = 24
}

int test_ternary(int n) {
    // abs(n) via ternary, and a nested ternary for sign.
    int mag  = n < 0 ? -n : n;
    int sign = n < 0 ? -1 : n > 0 ? 1 : 0;
    return mag * sign;  // returns n
}

int test_break_continue(void) {
    int sum = 0;
    for (int i = 0; i < LIMIT; i = i + 1) {
        if (i == 3) continue;   // skip 3
        if (i == 7) break;      // stop at 7
        sum = sum + i;
    }
    // 0+1+2+4+5+6 = 18
    return sum;
}

int test_string(void) {
    char buf[] = "hi";          // size inferred (3: 'h','i','\0')
    char pad[6] = "ab";         // explicit size, NUL + zero-padded tail
    return buf[0] + buf[1] + pad[0] + pad[1] + pad[2] + pad[5];
    // 'h'(104) + 'i'(105) + 'a'(97) + 'b'(98) + 0 + 0 = 404
}

int main(void) {
    int total = 0;
    total = total + test_inc_dec();        // 24
    total = total + test_ternary(-5);      // -5
    total = total + test_break_continue(); // 18
    total = total + test_string();         // 404
    // 24 - 5 + 18 + 404 = 441
    return total;
}
