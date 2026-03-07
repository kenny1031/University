#include <assert.h>
#include "lib.h"
#include <string.h>
#include <stdio.h>

int main() {
    // TODO: YOUR TEST CASES
    
    char str1[] = "Hello, World!";
    char str2[] = "resting 1 \n shhxD";
    char str3[] = "dhsj\0 siiiej";
    char* arr[] = {str1, str2, str3};
    size_t count = sizeof(arr) / sizeof(arr[0]);
    shout(arr, count);
    for (size_t i = 0; i < count; i++)
        printf("%s\n", arr[i]);
    assert(strcmp(str1, "HELLO, WORLD!") == 0);
    
}