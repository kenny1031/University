#include <errno.h>
#include <stdio.h>

int main() {
    errno = 0;
    FILE* fp = fopen("fakefile.txt", "r");
    if (errno != 0) perror("Error occurred");
    else fclose(fp);
}
