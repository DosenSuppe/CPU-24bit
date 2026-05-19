// malloc.h — dynamic-allocation interface for the cc.py C runtime.
//
// Implemented in heap.c (bump allocator) + _heap_start.asm. Link both
// alongside any program that includes this header.
//
// Sizes are in 24-bit WORDS, not bytes. Use sizeof(T) to compute counts:
//
//     struct Node *n = (struct Node *)malloc(sizeof(struct Node));
//     int *buf = (int *)malloc(sizeof(int) * 100);
//
// `free(p)` is currently a no-op (bump allocator can't reclaim individual
// blocks); call it anyway so swapping in a real free-list allocator later
// requires no code changes at the call site.

#pragma once

extern int *malloc(int n_words);
extern void free(int *p);
