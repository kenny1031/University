#include "lib.h"
#include <stdio.h>
#include <stddef.h>
#include <errno.h>
#include <stdlib.h>

size_t my_strlen(const char *str) {
    if (str == NULL) {
        errno = EINVAL; // invalid argument
        return (size_t)-1; // signal error with max size_t
    }
    size_t len = 0;
    while (str[len] != '\0') len++;
    return len;
}

int my_strcmp(const char *s1, const char *s2) {
    if (!s1 || !s2) return -1;
    size_t len1 = my_strlen(s1), len2 = my_strlen(s2);
    char unmatch1, unmatch2;
    for (int i = 0; i < len1 + 1; i++) {
        if (s1[i] != s2[i]) {
            unmatch1 = s1[i];
            unmatch2 = s2[i];
            return ((int)unmatch1 - (int)unmatch2);
        }
    }
    return 0;
}

int my_strncmp(const char *s1, const char *s2, size_t n) {
    if (!s1 || !s2) return -1;
    char unmatch1, unmatch2;
    for (int i = 0; i < n; i++) {
        if (s1[i] != s2[i]) {
            unmatch1 = s1[i];
            unmatch2 = s2[i];
            return ((int)unmatch1 - (int)unmatch2);
        }
    }
    return 0;
}

char *my_strcpy(char *dest, const char *src) {
    if (!dest || !src) return NULL;
    // make a copy of the pointer to the start of dest
    // for return purpose
    char *original = dest;
    // Copy data including null terminator
    while(*src != '\0') {
        *dest = *src;
        dest++; src++;
    }
    *dest = '\0';
    // Return the pointer to the start of dest
    return original;
}

char *my_strncpy(char *dest, const char *src, size_t n) {
    if (!dest || !src) return NULL;
    int i;
    for (i = 0; i < n && *(src + i) != '\0'; i++) {
        *(dest + i) = *(src + i);
    }
    while (i < n) {
        dest[i++] = '\0';
    }
    return dest;
}

char *my_strcat(char *dest, const char *src) {
    if (!dest || !src) return NULL;
    char *original = dest;
    while (*dest != '\0') dest++;
    while (*src != '\0') {
        *dest = *src;
        src++; dest++;
    }
    *dest = '\0';
    return original;
}

char *my_strncat(char *dest, const char *src, size_t n) {
    if (!dest || !src) return NULL;
    char *original = dest;
    while (*dest != '\0') dest++;
    int i;
    for (i = 0; i < n && *(src + i) != '\0'; i++) {
        *(dest + i) = *(src + i);
    }
    *(dest + i) = '\0';
    return original;
}
