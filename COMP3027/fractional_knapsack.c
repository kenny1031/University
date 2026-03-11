#include <stdio.h>
#include <stdlib.h>

typedef struct {
    double value;
    double weight;
    double density;
    int index;  // original index
} Item;

static int cmp_density_desc(const void *a, const void *b) {
    const Item *ia = (const Item *)a;
    const Item *ib = (const Item *)b;

    // sort by density descending
    if (ia->density < ib->density) return 1;
    if (ia->density > ib->density) return -1;
    return 0;
}

typedef struct {
    int index;
    double fraction;  // in [0, 1]
} Take;

double fractional_knapsack(
    Item *items, 
    int n, 
    double capacity, 
    Take *take, 
    int *take_count
) {
    if (capacity < 0) {
        fprintf(stderr, "Error: capacity must be non-negative\n");
        exit(1);
    }

    // compute density
    for (int i = 0; i < n; i++) {
        if (items[i].weight <= 0) {
            fprintf(stderr, "Error: all weights must be positive");
            exit(1);
        }
        items[i].density = items[i].value / items[i].weight;
    }

    // sort by the density descending
    qsort(items, n, sizeof(Item), cmp_density_desc);

    double remaining = capacity;
    double total_value = 0.0;
    *take_count = 0;

    for (int i = 0; i < n && remaining > 0; i++) {
        if (items[i].weight <= remaining) {
            // take whole
            total_value += items[i].value;
            remaining -= items[i].weight;
            take[*take_count].index = items[i].index;
            take[*take_count].fraction = 1.0;
            (*take_count)++;
        } else {
            // take fraction
            double frac = remaining / items[i].weight;
            total_value += items[i].value * frac;
            take[*take_count].index = items[i].index;
            take[*take_count].fraction = frac;
            (*take_count)++;
            remaining = 0.0;
        }
    }
    
    return total_value;
}

int main(void) {
    Item items[] = {
        {60, 10, 0, 0},
        {100, 20, 0, 1},
        {120, 30, 0, 2}
    };

    int n = (int)(sizeof(items) / sizeof(items[0]));
    double capacity = 50;

    // At most n decisions
    Take take[3];
    int take_count = 0;

    double ans = fractional_knapsack(items, n, capacity, take, &take_count);

    printf("max value: %.6f\n", ans);
    printf("take plan (original_index, fraction):\n");
    for (int i = 0; i < take_count; i++)
        printf("  (%d, %.6f)\n", take[i].index, take[i].fraction);

    return 0;
}