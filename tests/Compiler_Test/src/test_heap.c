// Exercises the v1.3 additions:
//   - sizeof(type) and sizeof(expr) folding to compile-time constants
//   - (T)expr casts (parsed + analyzed; runtime no-op since every type is 1 word)
//   - malloc / free via the bump allocator in heap.c
//   - Dynamic linked list built on the heap (the original motivation)
//
// Build:
//   cc.py heap.c        --no-entry      ; allocator (no main)
//   cc.py test_heap.c                   ; this file (has main)
//   compile + link  heap.obj + test_heap.obj + _heap_start.obj
//
// Expected return: REA = 200 when main halts.

#include "malloc.h"

struct Node {
    int val;
    struct Node *next;
};

// --- 1. sizeof folds to compile-time constants ------------------------
// Each call returns the WORD size of the type/expression. All scalars
// and pointers are 1 word; struct Node is 2 words.
int test_sizeof(void) {
    int total = 0;
    total = total + sizeof(int);              //  1
    total = total + sizeof(char);             //  1
    total = total + sizeof(int *);            //  1
    total = total + sizeof(struct Node);      //  2  (val + next)
    total = total + sizeof(struct Node *);    //  1
    int x;
    total = total + sizeof(x);                //  1  (sizeof of an expression)
    total = total + sizeof x;                 //  1  (no parens — equally valid)
    struct Node n;
    total = total + sizeof(n);                //  2
    total = total + sizeof(n.val);            //  1
    return total;                              // 11
}

// --- 2. Casts as compile-time noise --------------------------------------
// Bit-pattern stays the same; only the type the analyzer assigns changes.
// Useful with malloc (which returns int*) when you want a typed pointer.
int test_casts(void) {
    int x = 7;
    int *p = &x;
    char *cp = (char *)p;          // reinterpret int* as char*
    int *back = (int *)cp;         // and back
    return *back + (int)42;        // 7 + 42 = 49
}

// --- 3. Dynamic linked list on the heap ----------------------------------
// Build [1 -> 2 -> 3 -> NULL] using three malloc calls, then sum the
// values by traversing pointers.
int test_linked_heap(void) {
    struct Node *head;
    struct Node *cur;

    // Allocate three nodes via malloc + cast.
    head = (struct Node *)malloc(sizeof(struct Node));
    head->val = 1;
    head->next = (struct Node *)malloc(sizeof(struct Node));
    head->next->val = 2;
    head->next->next = (struct Node *)malloc(sizeof(struct Node));
    head->next->next->val = 3;
    head->next->next->next = (struct Node *)0;

    // Traverse and sum.
    int total = 0;
    cur = head;
    while (cur != (struct Node *)0) {
        total = total + cur->val;
        cur = cur->next;
    }
    // free() is a no-op for the bump allocator; calls included to verify
    // it parses + links cleanly.
    free((int *)head);
    return total;                  // 1 + 2 + 3 = 6
}

// --- 4. Heap-allocated array of ints ------------------------------------
// Allocates 10 ints, fills with i*i, sums them. Exercises malloc with
// sizeof(int) * N and direct integer pointer indexing.
int test_heap_array(void) {
    int n = 10;
    int *arr = malloc(sizeof(int) * n);
    int i;
    for (i = 0; i < n; i++) {
        arr[i] = i * i;
    }
    int sum = 0;
    for (i = 0; i < n; i++) {
        sum = sum + arr[i];
    }
    return sum;                    // 0+1+4+9+16+25+36+49+64+81 = 285 -> but truncated below
}

int main(void) {
    int total = 0;
    total = total + test_sizeof();          //  11
    total = total + test_casts();           //  49
    total = total + test_linked_heap();     //   6
    total = total + test_heap_array();      // 285
    return total - 151;                      // 11+49+6+285 - 151 = 200
}
