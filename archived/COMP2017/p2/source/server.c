#define _POSIX_C_SOURCE 200809L
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include "../libs/document.h"
#include "../libs/markdown.h"

#define MAX_CLIENTS 32
#define MAX_USERNAME 64
#define MAX_COMMAND_SIZE 256
#define ROLES_FILE "roles.txt"
#define DOC_SAVE_FILE "doc.md"

typedef enum { 
    PERMISSION_READ, 
    PERMISSION_WRITE 
} permission_t;

typedef struct client_info {
    pid_t pid;
    char username[MAX_USERNAME];
    permission_t permission;
    int connected;
    char pipe_c2s[64]; // Client to server pipe name
    char pipe_s2c[64]; // Server to client pipe name
    int fd_r;          // File descriptor for reading from client
    int fd_w;          // File descriptor for writing to client
    pthread_t thread;  // Thread handling this client
} client_info;

typedef struct command_entry {
    char username[MAX_USERNAME];
    char command[MAX_COMMAND_SIZE];
    struct command_entry *next;
} command_entry;

// Global variables
static document *doc;        // The document being edited
static uint64_t interval_ms; // Time interval for broadcasting updates
static client_info *clients[MAX_CLIENTS]; // Array of connected clients
static int client_count = 0;              // Number of connected clients
static pthread_mutex_t clients_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t doc_mutex = PTHREAD_MUTEX_INITIALIZER;
static int running = 1; // Flag to control server running state

// Command queue
static command_entry *command_queue_head = NULL;
static command_entry *command_queue_tail = NULL;
static pthread_mutex_t queue_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t queue_cond = PTHREAD_COND_INITIALIZER;

// Forward declarations
void *client_thread(void *arg);
void *command_processor_thread(void *arg);
void *broadcast_thread(void *arg);
void sig_handler(int sig, siginfo_t *info, void *ctx);
int authenticate_user(const char *username, permission_t *permission);
void queue_command(const char *username, const char *command);
void process_command(const char *username, const char *command);
void broadcast_update(const char *username, const char *command, int success);
void remove_client(client_info *client);
void clean_exit(int code);
void handle_signal(int sig);

// Signal handler for client connections (SIGRTMIN)
void sig_handler(int sig, siginfo_t *info, void *ctx) {
    (void)sig;
    (void)ctx;

    pthread_mutex_lock(&clients_mutex);

    if (client_count >= MAX_CLIENTS) {
        fprintf(stderr, "Maximum number of clients reached\n");
        pthread_mutex_unlock(&clients_mutex);
        return;
    }

    client_info *ci = calloc(1, sizeof(*ci));
    if (!ci) {
        perror("Failed to allocate client info");
        pthread_mutex_unlock(&clients_mutex);
        return;
    }

    ci->pid = info->si_pid;
    ci->connected = 1;
    snprintf(ci->pipe_c2s, sizeof(ci->pipe_c2s), "FIFO_C2S_%d", ci->pid);
    snprintf(ci->pipe_s2c, sizeof(ci->pipe_s2c), "FIFO_S2C_%d", ci->pid);

    clients[client_count++] = ci;

    pthread_mutex_unlock(&clients_mutex);

    // Create a new thread to handle this client
    pthread_create(&ci->thread, NULL, client_thread, ci);
}

// Signal handler for graceful shutdown
void handle_signal(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        printf("Received signal %d, shutting down...\n", sig);
        running = 0;
    }
}

// Setup signal handlers
void setup_signals() {
    // Handler for client connection requests (SIGRTMIN)
    struct sigaction sa = {.sa_sigaction = sig_handler, .sa_flags = SA_SIGINFO};
    sigemptyset(&sa.sa_mask);
    sigaction(SIGRTMIN, &sa, NULL);

    // Handler for graceful shutdown (SIGINT, SIGTERM)
    struct sigaction sa_term = {.sa_handler = handle_signal};
    sigemptyset(&sa_term.sa_mask);
    sigaction(SIGINT, &sa_term, NULL);
    sigaction(SIGTERM, &sa_term, NULL);

    // Block SIGPIPE so we don't terminate when a client disconnects
    sigset_t set;
    sigemptyset(&set);
    sigaddset(&set, SIGPIPE);
    pthread_sigmask(SIG_BLOCK, &set, NULL);
}

// Parse roles file and authenticate user
int authenticate_user(const char *username, permission_t *permission) {
    FILE *f = fopen(ROLES_FILE, "r");
    if (!f) {
        perror("Error opening roles file");
        return 0;
    }

    char line[256];
    char file_username[MAX_USERNAME];
    char perm_str[32];
    int found = 0;

    while (fgets(line, sizeof(line), f) != NULL) {
        // Remove trailing newline
        size_t len = strlen(line);
        if (len > 0 && line[len - 1] == '\n') {
            line[len - 1] = '\0';
        }

        // Parse username and permission
        if (sscanf(line, "%s %s", file_username, perm_str) != 2) {
            continue;
        }

        // Case-sensitive comparison as specified
        if (strcmp(username, file_username) == 0) {
            found = 1;
            if (strcmp(perm_str, "write") == 0) {
                *permission = PERMISSION_WRITE;
            } else if (strcmp(perm_str, "read") == 0) {
                *permission = PERMISSION_READ;
            } else {
                found = 0; // Invalid permission
            }
            break;
        }
    }

    fclose(f);
    return found;
}

// Client handler thread
void *client_thread(void *arg) {
    client_info *ci = (client_info *)arg;

    // Create FIFOs
    if (mkfifo(ci->pipe_c2s, 0666) == -1 && errno != EEXIST) {
        perror("Failed to create client-to-server FIFO");
        remove_client(ci);
        return NULL;
    }

    if (mkfifo(ci->pipe_s2c, 0666) == -1 && errno != EEXIST) {
        perror("Failed to create server-to-client FIFO");
        unlink(ci->pipe_c2s);
        remove_client(ci);
        return NULL;
    }

    // Signal client that FIFOs are ready
    kill(ci->pid, SIGRTMIN + 1);

    // Open pipes (order matters to avoid deadlock)
    ci->fd_w = open(ci->pipe_s2c, O_WRONLY);
    if (ci->fd_w == -1) {
        perror("Failed to open server-to-client FIFO");
        unlink(ci->pipe_c2s);
        unlink(ci->pipe_s2c);
        remove_client(ci);
        return NULL;
    }

    ci->fd_r = open(ci->pipe_c2s, O_RDONLY);
    if (ci->fd_r == -1) {
        perror("Failed to open client-to-server FIFO");
        close(ci->fd_w);
        unlink(ci->pipe_c2s);
        unlink(ci->pipe_s2c);
        remove_client(ci);
        return NULL;
    }

    // Read username (terminated by newline)
    char buffer[MAX_USERNAME];
    ssize_t bytes_read = read(ci->fd_r, buffer, sizeof(buffer) - 1);
    if (bytes_read <= 0) {
        perror("Failed to read username");
        close(ci->fd_r);
        close(ci->fd_w);
        unlink(ci->pipe_c2s);
        unlink(ci->pipe_s2c);
        remove_client(ci);
        return NULL;
    }

    buffer[bytes_read] = '\0';

    // Remove trailing newline
    char *newline = strchr(buffer, '\n');
    if (newline)
        *newline = '\0';

    strncpy(ci->username, buffer, sizeof(ci->username) - 1);
    ci->username[sizeof(ci->username) - 1] = '\0';

    // Authenticate user via roles.txt
    if (!authenticate_user(ci->username, &ci->permission)) {
        // Send rejection message
        dprintf(ci->fd_w, "Reject UNAUTHORISED\n");

        // Wait for 1 second before closing
        sleep(1);

        close(ci->fd_r);
        close(ci->fd_w);
        unlink(ci->pipe_c2s);
        unlink(ci->pipe_s2c);
        remove_client(ci);
        return NULL;
    }

    // Send role + newline
    const char *role_str =
        (ci->permission == PERMISSION_WRITE) ? "write" : "read";
    dprintf(ci->fd_w, "%s\n", role_str);

    // Send document version and content
    pthread_mutex_lock(&doc_mutex);
    uint64_t version = doc->current_version;
    char *content = markdown_flatten(doc);
    pthread_mutex_unlock(&doc_mutex);

    if (!content)
        content = strdup("");

    size_t content_len = strlen(content);
    dprintf(ci->fd_w, "%lu\n%zu\n%s", version, content_len, content);
    free(content);

    printf("Client %s connected with %s permission\n", ci->username, role_str);

    // Main command loop
    char cmd[MAX_COMMAND_SIZE];
    memset(cmd, 0, sizeof(cmd));

    while (running && ci->connected) {
        bytes_read = read(ci->fd_r, cmd, sizeof(cmd) - 1);

        if (bytes_read <= 0) {
            if (bytes_read == 0) {
                printf("Client %s disconnected\n", ci->username);
            } else {
                perror("Error reading from client");
            }
            break;
        }

        cmd[bytes_read] = '\0';

        // Check for trailing newline and remove it
        if (bytes_read > 0 && cmd[bytes_read - 1] == '\n') {
            cmd[bytes_read - 1] = '\0';
        }

        // Process command
        if (ci->permission == PERMISSION_WRITE || strncmp(cmd, "DOC", 3) == 0) {
            queue_command(ci->username, cmd);
        } else {
            // Send rejection for unauthorised command
            dprintf(ci->fd_w, "Reject UNAUTHORISED\n");
        }
    }

    // Clean up
    close(ci->fd_r);
    close(ci->fd_w);
    unlink(ci->pipe_c2s);
    unlink(ci->pipe_s2c);
    remove_client(ci);

    return NULL;
}

// Add command to queue
void queue_command(const char *username, const char *command) {
    command_entry *entry = malloc(sizeof(command_entry));
    if (!entry) {
        perror("Failed to allocate command entry");
        return;
    }

    strncpy(entry->username, username, sizeof(entry->username) - 1);
    entry->username[sizeof(entry->username) - 1] = '\0';

    strncpy(entry->command, command, sizeof(entry->command) - 1);
    entry->command[sizeof(entry->command) - 1] = '\0';

    entry->next = NULL;

    pthread_mutex_lock(&queue_mutex);

    if (command_queue_tail) {
        command_queue_tail->next = entry;
    } else {
        command_queue_head = entry;
    }

    command_queue_tail = entry;

    pthread_cond_signal(&queue_cond);
    pthread_mutex_unlock(&queue_mutex);
}

// Command processor thread
void *command_processor_thread(void *arg) {
    (void)arg;

    while (running) {
        pthread_mutex_lock(&queue_mutex);

        while (command_queue_head == NULL && running) {
            pthread_cond_wait(&queue_cond, &queue_mutex);
        }

        if (!running) {
            pthread_mutex_unlock(&queue_mutex);
            break;
        }

        command_entry *entry = command_queue_head;
        command_queue_head = entry->next;

        if (command_queue_head == NULL) {
            command_queue_tail = NULL;
        }

        pthread_mutex_unlock(&queue_mutex);

        // Process the command
        process_command(entry->username, entry->command);

        free(entry);
    }

    return NULL;
}

// Process a command
void process_command(const char *username, const char *command) {
    char cmd_type[32];
    int result = -1;

    if (sscanf(command, "%31s", cmd_type) != 1) {
        broadcast_update(username, command, 0);
        return;
    }

    pthread_mutex_lock(&doc_mutex);

    // Handle different command types
    if (strcmp(cmd_type, "INSERT") == 0) {
        size_t pos;
        char content[MAX_COMMAND_SIZE];

        if (sscanf(command, "INSERT %zu %[^\n]", &pos, content) == 2) {
            result = markdown_insert(doc, doc->current_version, pos, content);
        }
    } else if (strcmp(cmd_type, "DEL") == 0) {
        size_t pos, len;

        if (sscanf(command, "DEL %zu %zu", &pos, &len) == 2) {
            result = markdown_delete(doc, doc->current_version, pos, len);
        }
    } else if (strcmp(cmd_type, "NEWLINE") == 0) {
        size_t pos;

        if (sscanf(command, "NEWLINE %zu", &pos) == 1) {
            result = markdown_newline(doc, doc->current_version, pos);
        }
    } else if (strcmp(cmd_type, "HEADING") == 0) {
        size_t level, pos;

        if (sscanf(command, "HEADING %zu %zu", &level, &pos) == 2) {
            result = markdown_heading(doc, doc->current_version, level, pos);
        }
    } else if (strcmp(cmd_type, "BOLD") == 0) {
        size_t start, end;

        if (sscanf(command, "BOLD %zu %zu", &start, &end) == 2) {
            result = markdown_bold(doc, doc->current_version, start, end);
        }
    } else if (strcmp(cmd_type, "ITALIC") == 0) {
        size_t start, end;

        if (sscanf(command, "ITALIC %zu %zu", &start, &end) == 2) {
            result = markdown_italic(doc, doc->current_version, start, end);
        }
    } else if (strcmp(cmd_type, "BLOCKQUOTE") == 0) {
        size_t pos;

        if (sscanf(command, "BLOCKQUOTE %zu", &pos) == 1) {
            result = markdown_blockquote(doc, doc->current_version, pos);
        }
    } else if (strcmp(cmd_type, "ORDERED_LIST") == 0) {
        size_t pos;

        if (sscanf(command, "ORDERED_LIST %zu", &pos) == 1) {
            result = markdown_ordered_list(doc, doc->current_version, pos);
        }
    } else if (strcmp(cmd_type, "UNORDERED_LIST") == 0) {
        size_t pos;

        if (sscanf(command, "UNORDERED_LIST %zu", &pos) == 1) {
            result = markdown_unordered_list(doc, doc->current_version, pos);
        }
    } else if (strcmp(cmd_type, "CODE") == 0) {
        size_t start, end;

        if (sscanf(command, "CODE %zu %zu", &start, &end) == 2) {
            result = markdown_code(doc, doc->current_version, start, end);
        }
    } else if (strcmp(cmd_type, "HORIZONTAL_RULE") == 0) {
        size_t pos;

        if (sscanf(command, "HORIZONTAL_RULE %zu", &pos) == 1) {
            result = markdown_horizontal_rule(doc, doc->current_version, pos);
        }
    } else if (strcmp(cmd_type, "LINK") == 0) {
        size_t start, end;
        char url[MAX_COMMAND_SIZE];

        if (sscanf(command, "LINK %zu %zu %s", &start, &end, url) == 3) {
            result = markdown_link(doc, doc->current_version, start, end, url);
        }
    } else if (strcmp(cmd_type, "DOC") == 0) {
        // Special case for DOC command - just print current document state
        result = 0;
    } else {
        // Unknown command
        result = -1;
    }

    // If command was successful and modified the document, increment version
    if (result == SUCCESS && strcmp(cmd_type, "DOC") != 0) {
        markdown_increment_version(doc);
    }

    pthread_mutex_unlock(&doc_mutex);

    // Broadcast result to all clients
    broadcast_update(username, command, result == SUCCESS);
}

// Broadcast update to all clients
void broadcast_update(const char *username, const char *command, int success) {
    pthread_mutex_lock(&doc_mutex);
    uint64_t version = doc->current_version;
    pthread_mutex_unlock(&doc_mutex);

    // For DOC command, send the full document to the requesting client
    if (strcmp(command, "DOC") == 0) {
        pthread_mutex_lock(&clients_mutex);

        for (int i = 0; i < client_count; i++) {
            if (clients[i] && clients[i]->connected &&
                strcmp(clients[i]->username, username) == 0) {

                pthread_mutex_lock(&doc_mutex);
                char *content = markdown_flatten(doc);
                pthread_mutex_unlock(&doc_mutex);

                if (!content)
                    content = strdup("");

                dprintf(clients[i]->fd_w, "VERSION %lu\n", version);
                dprintf(clients[i]->fd_w, "EDIT %s %s SUCCESS\n", username,
                        command);
                dprintf(clients[i]->fd_w, "%s\n", content);
                dprintf(clients[i]->fd_w, "END\n");

                free(content);
                break;
            }
        }

        pthread_mutex_unlock(&clients_mutex);
        return;
    }

    // Prepare broadcast message
    char message[MAX_COMMAND_SIZE + 128];
    snprintf(message, sizeof(message), "VERSION %lu\nEDIT %s %s %s\nEND\n",
             version, username, command, success ? "SUCCESS" : "Reject");

    // Send to all connected clients
    pthread_mutex_lock(&clients_mutex);

    for (int i = 0; i < client_count; i++) {
        if (clients[i] && clients[i]->connected) {
            write(clients[i]->fd_w, message, strlen(message));
        }
    }

    pthread_mutex_unlock(&clients_mutex);
}

// Broadcast thread - periodically broadcasts version updates
void *broadcast_thread(void *arg) {
    (void)arg; // Unused

    while (running) {
        // Sleep for the specified interval
        struct timespec ts = {.tv_sec = interval_ms / 1000,
                              .tv_nsec = (interval_ms % 1000) * 1000000};
        nanosleep(&ts, NULL);

        // Increment document version
        pthread_mutex_lock(&doc_mutex);
        markdown_increment_version(doc);
        uint64_t version = doc->current_version;
        pthread_mutex_unlock(&doc_mutex);

        // Broadcast version update to all clients
        char message[64];
        snprintf(message, sizeof(message), "VERSION %lu\nEND\n", version);

        pthread_mutex_lock(&clients_mutex);

        for (int i = 0; i < client_count; i++) {
            if (clients[i] && clients[i]->connected) {
                write(clients[i]->fd_w, message, strlen(message));
            }
        }

        pthread_mutex_unlock(&clients_mutex);
    }

    return NULL;
}

// Remove a client from the clients array
void remove_client(client_info *client) {
    pthread_mutex_lock(&clients_mutex);

    for (int i = 0; i < client_count; i++) {
        if (clients[i] == client) {
            // Mark as disconnected first
            clients[i]->connected = 0;

            // Free the client info and remove from array
            free(clients[i]);

            // Move last client to this position
            if (i < client_count - 1) {
                clients[i] = clients[client_count - 1];
            }

            client_count--;
            break;
        }
    }

    pthread_mutex_unlock(&clients_mutex);
}

// Clean up and exit
void clean_exit(int code) {
    // Set running flag to false to stop threads
    running = 0;

    // Signal command processor to wake up
    pthread_cond_signal(&queue_cond);

    // Clean up clients
    pthread_mutex_lock(&clients_mutex);

    for (int i = 0; i < client_count; i++) {
        if (clients[i]) {
            if (clients[i]->connected) {
                close(clients[i]->fd_r);
                close(clients[i]->fd_w);
                unlink(clients[i]->pipe_c2s);
                unlink(clients[i]->pipe_s2c);
            }
            free(clients[i]);
        }
    }

    client_count = 0;
    pthread_mutex_unlock(&clients_mutex);

    // Clean up command queue
    pthread_mutex_lock(&queue_mutex);

    command_entry *entry = command_queue_head;
    while (entry) {
        command_entry *next = entry->next;
        free(entry);
        entry = next;
    }

    command_queue_head = NULL;
    command_queue_tail = NULL;

    pthread_mutex_unlock(&queue_mutex);

    // Free document
    if (doc) {
        // Save document to file
        FILE *f = fopen(DOC_SAVE_FILE, "w");
        if (f) {
            markdown_print(doc, f);
            fclose(f);
        }

        markdown_free(doc);
    }

    // Destroy mutexes and condition variables
    pthread_mutex_destroy(&clients_mutex);
    pthread_mutex_destroy(&doc_mutex);
    pthread_mutex_destroy(&queue_mutex);
    pthread_cond_destroy(&queue_cond);

    exit(code);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <interval-ms>\n", argv[0]);
        return EXIT_FAILURE;
    }

    interval_ms = strtoull(argv[1], NULL, 10);
    if (interval_ms == 0) {
        fprintf(stderr, "Invalid interval: must be a positive integer\n");
        return EXIT_FAILURE;
    }

    // Setup signal handlers
    setup_signals();

    // Initialise document
    doc = markdown_init();
    if (!doc) {
        fprintf(stderr, "Failed to initialize document\n");
        return EXIT_FAILURE;
    }

    // Print server PID
    printf("Server PID: %d\n", getpid());
    fflush(stdout);

    // Create command processor thread
    pthread_t cmd_processor_tid;
    if (pthread_create(&cmd_processor_tid, NULL, command_processor_thread,
                       NULL) != 0) {
        perror("Failed to create command processor thread");
        markdown_free(doc);
        return EXIT_FAILURE;
    }

    // Create broadcast thread
    pthread_t broadcast_tid;
    if (pthread_create(&broadcast_tid, NULL, broadcast_thread, NULL) != 0) {
        perror("Failed to create broadcast thread");
        running = 0;
        pthread_cond_signal(&queue_cond);
        pthread_join(cmd_processor_tid, NULL);
        markdown_free(doc);
        return EXIT_FAILURE;
    }

    // Handle QUIT command from terminal
    char buffer[32];
    while (running) {
        if (fgets(buffer, sizeof(buffer), stdin) == NULL) {
            if (feof(stdin)) {
                break;
            }
            perror("Error reading from stdin");
            continue;
        }

        // Remove trailing newline
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') {
            buffer[len - 1] = '\0';
        }

        if (strcmp(buffer, "QUIT") == 0) {
            if (client_count > 0) {
                printf("QUIT rejected, %d clients still connected.\n",
                       client_count);
            } else {
                printf("Shutting down server...\n");
                running = 0;
                break;
            }
        }
    }

    // Wait for threads to finish
    pthread_cond_signal(&queue_cond);
    pthread_join(cmd_processor_tid, NULL);
    pthread_join(broadcast_tid, NULL);

    clean_exit(0);

    return EXIT_SUCCESS;
}