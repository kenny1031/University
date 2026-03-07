#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

static volatile sig_atomic_t ready = 0;

void sig_ready(int sig) {
    (void)sig;
    ready = 1;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <server_pid> <username>\n", argv[0]);
        return EXIT_FAILURE;
    }

    pid_t server_pid = (pid_t)atoi(argv[1]);
    const char *username = argv[2];

    // Setup handler for SIGRTMIN+1
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = sig_ready;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    if (sigaction(SIGRTMIN + 1, &sa, NULL) == -1) {
        perror("sigaction");
        return EXIT_FAILURE;
    }

    // Notify server to create FIFOs
    if (kill(server_pid, SIGRTMIN) == -1) {
        perror("kill");
        return EXIT_FAILURE;
    }

    // Wait for server signal
    while (!ready) {
        pause();
    }

    // Print out FIFO names
    char fifo_c2s[64];
    char fifo_s2c[64];
    pid_t client_pid = getpid();
    snprintf(fifo_c2s, sizeof(fifo_c2s), "FIFO_C2S_%d", client_pid);
    snprintf(fifo_s2c, sizeof(fifo_s2c), "FIFO_S2C_%d", client_pid);

    // Open server-to-client FIFO for reading first
    int fd_r = open(fifo_s2c, O_RDONLY);
    if (fd_r == -1) {
        fprintf(stderr, "Failed to open %s for reading: %s\n", fifo_s2c,
                strerror(errno));
        return EXIT_FAILURE;
    }

    // Then open client-to-server FIFO for writing
    int fd_w = open(fifo_c2s, O_WRONLY);
    if (fd_w == -1) {
        fprintf(stderr, "Failed to open %s for writing: %s\n", fifo_c2s,
                strerror(errno));
        close(fd_r);
        return EXIT_FAILURE;
    }

    // Send username (newline-terminated)
    dprintf(fd_w, "%s\n", username);

    // Line-oriented input
    FILE *srv = fdopen(fd_r, "r");
    if (!srv) {
        perror("fdopen");
        close(fd_r);
        close(fd_w);
        return EXIT_FAILURE;
    }

    // Read role line
    char role[32];
    if (!fgets(role, sizeof(role), srv)) {
        fprintf(stderr, "Failed to read role\n");
        fclose(srv);
        close(fd_w);
        return EXIT_FAILURE;
    }
    // Strip newline
    role[strcspn(role, "\r\n")] = '\0';

    // Check for rejection
    if (strncmp(role, "Reject", 6) == 0) {
        fprintf(stderr, "Server response: %s\n", role);
        fclose(srv);
        close(fd_w);
        return EXIT_FAILURE;
    }

    int can_write = (strcmp(role, "write") == 0);

    // Read version
    char line[64];
    if (!fgets(line, sizeof(line), srv)) {
        fprintf(stderr, "Failed to read version\n");
        fclose(srv);
        close(fd_w);
        return EXIT_FAILURE;
    }
    uint64_t version = strtoull(line, NULL, 10);

    // Read document length
    if (!fgets(line, sizeof(line), srv)) {
        fprintf(stderr, "Failed to read document length\n");
        fclose(srv);
        close(fd_w);
        return EXIT_FAILURE;
    }
    size_t doclen = strtoull(line, NULL, 10);

    // Read document content
    char *docbuf = malloc(doclen + 1);
    if (!docbuf) {
        perror("malloc");
        fclose(srv);
        close(fd_w);
        return EXIT_FAILURE;
    }
    size_t total = 0;
    while (total < doclen) {
        ssize_t r = fread(docbuf + total, 1, doclen - total, srv);
        if (r <= 0)
            break;
        total += r;
    }
    docbuf[total] = '\0';

    // Print initial document
    printf("[Version %llu]\n", (unsigned long long)version);
    fwrite(docbuf, 1, total, stdout);
    printf("\n");
    free(docbuf);

    // Prepare for multiplexed I/O
    fd_set rfds;
    int maxfd = (fd_r > STDIN_FILENO) ? fd_r : STDIN_FILENO;

    // Set stdout to be unbuffered
    setbuf(stdout, NULL);

    while (1) {
        FD_ZERO(&rfds);
        FD_SET(STDIN_FILENO, &rfds);
        FD_SET(fd_r, &rfds);

        int ret = select(maxfd + 1, &rfds, NULL, NULL, NULL);
        if (ret < 0) {
            if (errno == EINTR)
                continue;
            perror("select");
            break;
        }

        // User input: send commands
        if (FD_ISSET(STDIN_FILENO, &rfds)) {
            char cmd[512];
            if (!fgets(cmd, sizeof(cmd), stdin)) {
                // EOF or error
                break;
            }
            size_t len = strlen(cmd);
            if (len == 0)
                continue;
            // If no write permission, skip commands except DOC?
            if (!can_write) {
                if (!(strncmp(cmd, "DOC?", 4) == 0 ||
                      strncmp(cmd, "PERM?", 5) == 0 ||
                      strncmp(cmd, "LOG?", 4) == 0)) {
                    fprintf(stderr, "Unauthorized command: %s", cmd);
                    continue;
                }
            }
            ssize_t w = write(fd_w, cmd, len);
            if (w < 0) {
                perror("write to server");
                break;
            }
        }

        // Server message
        if (FD_ISSET(fd_r, &rfds)) {
            char buf[1024];
            if (fgets(buf, sizeof(buf), srv) == NULL) {
                break;
            }
            fputs(buf, stdout);
        }
    }

    fclose(srv);
    close(fd_w);
    return EXIT_SUCCESS;
}