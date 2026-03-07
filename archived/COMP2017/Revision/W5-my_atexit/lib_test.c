#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "lib.h"

void cleanup_str(void *arg) {
    char *str = (char *)arg;
    printf("Freeing: %s\n", str);
    free(str);
}

void print_msg(void *arg) {
    printf("Message: %s\n", (char *)arg);
}

int main() {
    char *msg1 = strdup("First");
    char *msg2 = strdup("Second");

    assert(register_exit_handler(cleanup_str, msg1) == 0);
    assert(register_exit_handler(cleanup_str, msg2) == 0);
    assert(register_exit_handler(print_msg, "All done!") == 0);

    // Handlers should be executed in reverse order:
    // 1. print_msg("All done!")
    // 2. cleanup_str(msg2)
    // 3. cleanup_str(msg1)
    execute_exit_handlers();

    printf("All handlers executed.\n");
    return 0;
}
