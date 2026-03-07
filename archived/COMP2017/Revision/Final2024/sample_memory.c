#include <stdlib.h>

struct rec {
    char  tag;
    int   *link;
};

int main(void)
{
    struct rec *p = malloc(sizeof(struct rec));
    p->tag   = 'A';
    p->link  = (int *)&p->tag;

    p        = realloc(p, 2 * sizeof(struct rec)); 
    p[1].tag = 'B';
    p[1].link = &p[0].tag;

    /* === GIVE A SNAPSHOT OF THE MEMORY HERE === */

}

