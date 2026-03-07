#include <stdlib.h>
#include <stdio.h>

struct dyn_arr {
    int* arr;
    size_t size;
    size_t length;
};

void append(struct dyn_arr* my_arr, int a) {
    my_arr->arr[my_arr->length] = a;
    my_arr->length++;
    
    if (my_arr->length == my_arr->size) {
        my_arr->size *= 2;
        my_arr->arr = (int *) realloc(my_arr->arr, my_arr->size * sizeof(int));
    }
}

int main() {
    struct dyn_arr* my_arr = (struct dyn_arr *) malloc(sizeof(struct dyn_arr));

    my_arr->size = 2;
    my_arr->length = 0;
    my_arr->arr = (int *) calloc(my_arr->size, sizeof(int));

    append(my_arr, 1);
    append(my_arr, 2);
    append(my_arr, 3);

    printf("%d %d %d\n", my_arr->arr[0], my_arr->arr[1], my_arr->arr[2]);
    printf("size: %ld\n", my_arr->size);

    free(my_arr->arr);
    free(my_arr);
}
