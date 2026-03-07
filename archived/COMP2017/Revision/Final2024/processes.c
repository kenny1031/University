#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

#define MAX_PROCESSES 100
#define MSG_LEN 50

static int current_index = 0;
static int process_num = 0;
int pipefds[MAX_PROCESSES - 1][2];

#define READ_FROM_CHILD pipefds[current_index - 1][0]
#define WRITE_TO_PARENT pipefds[current_index - 1][1]
#define READ_FROM_PARENT pipefds[current_index][0]
#define WRITE_TO_CHILD pipefds[current_index][1]

typedef enum { 
    FOR, // To child
    BACK, // To parent
} dir;

typedef struct {
    int src_id;
    int dest_id;
    char msg[50];
    dir direction;
} Message;

void create_children(int count, int pipefds[][2]) {
    for (int i = 0; i < count - 1; i++) {
        if (pipe(pipefds[i]) < 0) {
            perror("pipe");
            exit(1);
        }
    }

    for (int i = 0; i < count; i++) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork");
            exit(1);
        }
        if (pid == 0) {
            continue;
        } else {
            current_index = i;
            printf("P%d Created\n", current_index);
            break;
        }
    }
    process_num = count;
}

void send_message(int process, char *msg, int msg_len) {
    if (!msg) return;
    if (msg_len > MSG_LEN) msg_len = MSG_LEN;
    Message message;
    message.src_id = current_index;
    message.dest_id = process;
    strncpy(message.msg, msg, sizeof(message.msg));
    if (message.dest_id < current_index) {
        message.direction = BACK;
        write(WRITE_TO_PARENT, &message, sizeof(Message));
    } else if (message.dest_id > current_index) {
        message.direction = FOR;
        write(WRITE_TO_CHILD, &message, sizeof(Message));
    }
}

void receive_message(char *buffer, int *nread, int buffer_max) {
    if (!buffer || !nread) return;

    int tried = 0;
    *nread = 0;
    Message recv_msg;

    if (current_index > 0) {
        *nread = read(READ_FROM_CHILD, &recv_msg, sizeof(Message));
        tried = 1;
    }
    if (*nread <= 0 && current_index < process_num - 1) {
        *nread = read(READ_FROM_PARENT, &recv_msg, sizeof(Message));
        tried = 1;
    }
    if (*nread <= 0 || !tried) return;

    if (recv_msg.src_id == current_index) {
        // Drop the message — this is a looped-back message
        return;
    }

    // If we got here, we successfully read a message
    if (recv_msg.dest_id == current_index) {
        strncpy(buffer, recv_msg.msg, buffer_max);
        buffer[buffer_max - 1] = '\0';  // Ensure null-termination
    } else {
        send_message(recv_msg.dest_id, recv_msg.msg, MSG_LEN);
    }
}

void free_resources(void) {
    for (int i = 0; i < process_num - 1; i++) {
        if (i == current_index - 1 || i == current_index) {
            close(pipefds[i][0]);
            close(pipefds[i][1]);
        }
    }
}

void handle_sigterm(void) {
    free_resources();
    exit(0);
}

int main(void) {
    signal(SIGTERM, handle_sigterm);
    //create_children(5, pipefds);
}