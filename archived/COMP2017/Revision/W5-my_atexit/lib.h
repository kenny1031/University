#ifndef LIB_H
#define LIB_H

#include <stddef.h> // For size_t, NULL

// --- Type Definitions ---

// Function pointer type for exit handlers
// Takes a void pointer as an argument, allowing handlers to work with arbitrary data
typedef void (*ExitHandlerFunc)(void *arg);

// Node structure for the linked list of exit handlers
typedef struct ExitHandlerNode
{
    ExitHandlerFunc func;         // Pointer to the handler function
    void *arg;                    // Argument to pass to the handler function
    struct ExitHandlerNode *next; // Pointer to the next node in the list
} ExitHandlerNode;

// --- Function Prototypes ---

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
int register_exit_handler(ExitHandlerFunc func, void *arg);

/**
 * @brief Executes all registered exit handlers in LIFO order.
 *
 * Iterates through the list of registered handlers, calls each function
 * with its associated argument, and frees the memory associated with the
 * handler node. The list is empty after this function completes.
 */
void execute_exit_handlers(void);

#endif // LIB_H

