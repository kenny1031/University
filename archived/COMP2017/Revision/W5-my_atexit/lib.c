#include "lib.h"
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

static ExitHandlerNode *head = NULL;

/**
 * @brief Registers a function to be called by execute_exit_handlers.
 *
 * Functions are stored in a linked list and will be executed in LIFO
 * (Last-In, First-Out) order when execute_exit_handlers() is called.
 *
 * @param func The function pointer (of type ExitHandlerFunc) to register.
 * @param arg A void pointer to data that will be passed to the handler function
 *            when it is executed. Can be NULL if the handler doesn't need data.
 * @return 0 on successful registration.
 * @return -1 if memory allocation for the handler node fails.
 */
int register_exit_handler(ExitHandlerFunc func, void *arg) {
    ExitHandlerNode *new_node = malloc(sizeof(ExitHandlerNode));
    if (!new_node) return -1;
    new_node->func = func;
    new_node->arg = arg;
    new_node->next = head;
    head = new_node;

    return 0;
}

/**
 * @brief Executes all registered exit handlers in LIFO order.
 *
 * Iterates through the list of registered handlers, calls each function
 * with its associated argument, and frees the memory associated with the
 * handler node. The list is empty after this function completes.
 */
void execute_exit_handlers(void) {
    ExitHandlerNode *current = head;
    while (current) {
        current->func(current->arg);
        ExitHandlerNode *temp = current;
        current = current->next;
        free(temp);
    }
    head = NULL;
}

