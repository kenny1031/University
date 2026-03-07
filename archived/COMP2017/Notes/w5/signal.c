#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

#define MSG "Interrupted\n"

void sigint_handler(int signo, siginfo_t* sinfo, void* context) {
    (void) signo; (void) sinfo; (void) context;
    write(fileno(stdout), MSG, strlen(MSG));
}

int main() {
    struct sigaction sig = {0};

    sig.sa_sigaction = sigint_handler; // specifies the function
    sig.sa_flags = SA_SIGINFO;

    sigaction(SIGINT, &sig, NULL); // specifies the signal and action

    while (1);
}
