#include <stdlib.h>
#include <stdio.h>

#define SUCCESS 0
#define INVALID_POS -1

struct node {
    int data;
    struct node* next;
};
struct l_list {
    struct node* head;
};

struct node* l_init(int data) {
    struct node* elem = (struct node *) malloc(sizeof(struct node));
    elem->data = data;
    return elem;
}

void prepend(struct l_list* list, struct node* elem) {
    elem->next = list->head;
    list->head = elem;
}

int l_insert(struct l_list* list, struct node* elem, int pos) {
    if (pos == 0) {
        prepend(list, elem);
        return SUCCESS;
    }

    struct node* current = list->head;
    for (int i = 1; current != NULL && i < pos; i++) {
        current = current->next;
    }
    if (current == NULL) return INVALID_POS; // pos out of bounds

    elem->next = current->next;
    current->next = elem;
    return SUCCESS;
}

struct node* pop(struct l_list* list) {
    struct node* elem = list->head;
    if (elem == NULL) return NULL;

    list->head = elem->next;
    elem->next = NULL;
    return elem;
}

int l_remove(struct l_list* list, int pos) {
    if (pos == 0) {
        struct node* elem = pop(list);
        if (elem == NULL) return INVALID_POS;
        free(elem);
        return SUCCESS;
    }

    struct node* current = list->head;
    for (int i = 1; current != NULL && i < pos; i++) {
        current = current->next;
    }
    if (current == NULL) return INVALID_POS; // pos out of bounds

    struct node* elem = current->next;
    if (elem == NULL) return INVALID_POS;
    current->next = elem->next;
    free(elem);
    return SUCCESS;
}

void l_free(struct node* head) {
    struct node* current = head;
    while (current != NULL) {
        struct node* next = current->next;
        free(current);
        current = next;
    }
}

int main() {
    struct l_list* list = (struct l_list *) calloc(1, sizeof(struct l_list));
    prepend(list, l_init(3));
    prepend(list, l_init(2));
    prepend(list, l_init(1));

    struct node* current = list->head;
    while (current != NULL) {
        printf("%d ", current->data);
        current = current->next;
    } printf("\n");

    l_insert(list, l_init(-1), 1);
    l_insert(list, l_init(-2), 3);
    l_insert(list, l_init(-3), 5);

    current = list->head;
    while (current != NULL) {
        printf("%d ", current->data);
        current = current->next;
    } printf("\n");

    l_remove(list, 4);
    l_remove(list, 2);
    l_remove(list, 0);

    current = list->head;
    while (current != NULL) {
        printf("%d ", current->data);
        current = current->next;
    } printf("\n");

    l_free(list->head);
    free(list);
}
