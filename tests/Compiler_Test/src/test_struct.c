// Exercises every v1 struct feature:
//   - Top-level struct definitions
//   - Forward declarations (Node before its body)
//   - Self-referential type via pointer (linked list)
//   - Nested struct fields (Box contains Point)
//   - Local & global struct variables
//   - `.field` (direct) and `->field` (via pointer) access
//   - Arrays of struct (Point pts[3])
//   - Address-of-field (`&` on a member access)
//   - Field assignment, compound assignment, ++
//
// Each test_* returns an independent value; main aggregates them into a
// single number that should equal 1000 if everything works.

struct Node;   // forward declaration — used through pointer below

struct Point {
    int x;
    int y;
};

struct Box {
    int width;
    struct Point corner;   // nested struct by value (fine, complete here)
};

struct Node {
    int val;
    struct Node *next;     // self-reference via pointer
};

struct Point g_origin;     // zero-initialized global struct
struct Point g_pts[3];     // zero-initialized array of struct

// --- 1. Basic local struct: dot access, field write+read ---
int test_basic(void) {
    struct Point p;
    p.x = 3;
    p.y = 4;
    return p.x + p.y;          // 7
}

// --- 2. Global struct: write, then read through pointer ---
int sum_point(struct Point *p) {
    return p->x + p->y;
}
int test_global_and_ptr(void) {
    g_origin.x = 10;
    g_origin.y = 20;
    return sum_point(&g_origin);   // 30
}

// --- 3. Address-of-field passed as a plain pointer ---
int double_int(int *p) {
    *p = *p + *p;
    return *p;
}
int test_field_addr(void) {
    struct Point q;
    q.x = 11;
    q.y = 0;
    return double_int(&q.x) + q.x;   // 22 + 22 = 44
}

// --- 4. Nested struct: `.field.subfield` ---
int test_nested(void) {
    struct Box b;
    b.width = 100;
    b.corner.x = 5;
    b.corner.y = 10;
    return b.width + b.corner.x + b.corner.y;   // 115
}

// --- 5. Array of struct (local) ---
int test_array(void) {
    struct Point pts[3];
    int i;
    int total;
    i = 0;
    while (i < 3) {
        pts[i].x = i + 1;        // 1, 2, 3
        pts[i].y = (i + 1) * 2;  // 2, 4, 6
        i = i + 1;
    }
    total = 0;
    i = 0;
    while (i < 3) {
        total = total + pts[i].x + pts[i].y;
        i = i + 1;
    }
    return total;   // (1+2) + (2+4) + (3+6) = 18
}

// --- 6. Linked list using forward-declared self-referential struct ---
int test_linked(void) {
    struct Node a;
    struct Node b;
    struct Node c;
    a.val = 1; b.val = 2; c.val = 4;
    a.next = &b;
    b.next = &c;
    c.next = 0;       // NULL terminator
    // Traverse: 1 + 2 + 4 = 7
    return a.val + a.next->val + a.next->next->val;
}

// --- 7. Compound assignment & ++ on struct fields ---
int test_field_compound(void) {
    struct Point p;
    p.x = 5;
    p.y = 3;
    p.x += p.y;       // p.x = 8
    p.y *= 2;         // p.y = 6
    p.x++;            // p.x = 9
    --p.y;            // p.y = 5
    return p.x + p.y; // 14
}

// --- 8. Global array of struct ---
int test_global_array(void) {
    g_pts[0].x = 7;
    g_pts[1].x = 70;
    g_pts[2].x = 700;
    return g_pts[0].x + g_pts[1].x + g_pts[2].x;  // 777
}

int main(void) {
    int total = 0;
    total = total + test_basic();           //   7
    total = total + test_global_and_ptr();  //  30
    total = total + test_field_addr();      //  44
    total = total + test_nested();          // 115
    total = total + test_array();           //  18
    total = total + test_linked();          //   7
    total = total + test_field_compound();  //  14
    total = total + test_global_array();    // 777
    return total;                            // 1012  (NB: NOT 1000 — see note)
}
