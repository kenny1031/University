#include <assert.h>
#include "lib.h"
#include <stdio.h>
#include <string.h>

void test_strcpy() {
    // Test 1: Normal copy
    char buf1[20];
    my_strcpy(buf1, "hello");
    assert(strcmp(buf1, "hello") == 0);

    // Test 2: Empty source
    char buf2[10] = "abc";
    my_strcpy(buf2, "");
    assert(strcmp(buf2, "") == 0);

    // Test 3: Long string
    char buf3[50];
    my_strcpy(buf3, "1234567890abcdef");
    assert(strcmp(buf3, "1234567890abcdef") == 0);

    // Test 4: NULL input
    assert(my_strcpy(NULL, "test") == NULL);
    assert(my_strcpy(buf1, NULL) == NULL);

    printf("All tests passed!\n");
}

void test_strcat() {
    // Test 1: Normal concatenation
    char buf1[20] = "Hello, ";
    my_strcat(buf1, "World!");
    assert(strcmp(buf1, "Hello, World!") == 0);

    // Test 2: Append empty string
    char buf2[20] = "Base";
    my_strcat(buf2, "");
    assert(strcmp(buf2, "Base") == 0);

    // Test 3: Empty dest, non-empty src
    char buf3[20] = "";
    my_strcat(buf3, "CopyMe");
    assert(strcmp(buf3, "CopyMe") == 0);

    // Test 4: NULL input
    assert(my_strcat(NULL, "abc") == NULL);
    assert(my_strcat(buf1, NULL) == NULL);

    printf("All tests passed!\n");
}

void test_strncpy(void) {
    // Test 1: Normal copy, src shorter than n
    char dest1[10];
    my_strncpy(dest1, "abc", 6);
    assert(strcmp(dest1, "abc") == 0);         // content correct
    assert(dest1[3] == '\0');                  // explicit null terminator
    assert(dest1[4] == '\0');                  // padded with nulls

    // Test 2: src length exactly n
    char dest2[5];
    my_strncpy(dest2, "abcd", 4);
    assert(memcmp(dest2, "abcd", 4) == 0);     // no null terminator
    assert(dest2[3] == 'd');

    // Test 3: src longer than n
    char dest3[5];
    my_strncpy(dest3, "abcdef", 4);
    assert(memcmp(dest3, "abcd", 4) == 0);     // truncates correctly

    // Test 4: n == 0
    char dest4[5] = "zzzz";
    my_strncpy(dest4, "123", 0);
    assert(strcmp(dest4, "zzzz") == 0);        // unchanged

    // Test 5: src is empty string
    char dest5[4] = "xxx";
    my_strncpy(dest5, "", 3);
    assert(dest5[0] == '\0');
    assert(dest5[1] == '\0');
    assert(dest5[2] == '\0');

    // Test 6: NULL pointers (should return NULL)
    assert(my_strncpy(NULL, "abc", 3) == NULL);
    assert(my_strncpy(dest1, NULL, 3) == NULL);

    printf("All tests passed!\n");
}

void test_strncat(void) {
    // Test 1: Normal concatenation (src shorter than n)
    char buf1[20] = "Hello, ";
    my_strncat(buf1, "world!", 6);
    assert(strcmp(buf1, "Hello, world!") == 0);

    // Test 2: Truncation (n < src length)
    char buf2[20] = "Test: ";
    my_strncat(buf2, "abcdef", 3);
    assert(strcmp(buf2, "Test: abc") == 0);

    // Test 3: n == 0 (no change)
    char buf3[20] = "Keep";
    my_strncat(buf3, "THIS", 0);
    assert(strcmp(buf3, "Keep") == 0);

    // Test 4: Empty src string
    char buf4[20] = "Begin";
    my_strncat(buf4, "", 5);
    assert(strcmp(buf4, "Begin") == 0);

    // Test 5: Append empty dest string
    char buf5[20] = "";
    my_strncat(buf5, "Hi", 5);
    assert(strcmp(buf5, "Hi") == 0);

    // Test 6: NULL dest or src
    assert(my_strncat(NULL, "abc", 3) == NULL);
    assert(my_strncat(buf1, NULL, 3) == NULL);

    printf("All tests passed!\n");
}


int main() {
    // TODO: YOUR TEST CASES
    char *s1 = "h9f[] dfh";
    assert(my_strlen(s1) == strlen(s1));
    assert(my_strlen("") == 0);
    assert(my_strlen(NULL) == (size_t)-1);

    assert(my_strcmp("", "") == 0);
    assert(my_strcmp("TRue", "TRue") == 0);
    assert(my_strcmp("abcd", "abCd") > 0);
    assert(my_strcmp("Hello", "hello") < 0);
    assert(
        my_strcmp(NULL, "abc") == -1 ||
        my_strcmp("abc", NULL) == -1 ||
        my_strcmp(NULL, NULL) == -1
    );

    assert(my_strncmp("ABCD", "ABCE", 3) == 0);
    assert(my_strncmp("abcd", "abcde", 5) < 0);
    assert(my_strncmp("ahd", "sjc", 0) == 0);
    assert(
        my_strncmp(NULL, "abc", 2) == -1 ||
        my_strncmp("abc", NULL, 3) == -1 ||
        my_strncmp(NULL, NULL, 0) == -1
    );

    test_strcpy();
    test_strncpy();
    test_strcat();
    test_strncat();
}
