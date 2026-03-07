#include "lib.h"
#include <string.h>
#include <ctype.h>

void shout(char** strs, size_t no_str) {
    if (!strs || no_str == 0) return;

    for (size_t i = 0; i < no_str; i++) {
        char* s = strs[i];
        if (!s) continue;

        size_t len = strlen(s);
        for (size_t j = 0; j < len; j++) {
            s[j] = toupper((unsigned char)s[j]);
        }
    }
}