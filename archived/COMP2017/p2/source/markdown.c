#include "../libs/markdown.h"
#include "../libs/document.h"
#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// --- Local strdup replacements for portability ---
static char *md_strdup(const char *s) {
    size_t n = strlen(s);
    char *r = malloc(n + 1);
    if (r)
        memcpy(r, s, n + 1);
    return r;
}

// --- Pending Operations ---
typedef enum { 
    OP_INSERT, 
    OP_DELETE 
} OpType;

typedef struct Op {
    OpType type;
    size_t pos;
    size_t len; // for delete
    char *data; // for insert
    struct Op *next;
} Op;

typedef struct OpList {
    document *doc;
    Op *head;
    Op *tail;
    struct OpList *next;
} OpList;

static OpList *op_lists = NULL;

// get or create operation list for a document
static OpList *get_ops(document *doc) {
    for (OpList *p = op_lists; p; p = p->next) {
        if (p->doc == doc)
            return p;
    }
    OpList *node = malloc(sizeof(OpList));
    if (!node)
        return NULL;
    node->doc = doc;
    node->head = node->tail = NULL;
    node->next = op_lists;
    op_lists = node;
    return node;
}

// free all pending ops for a document
static void free_ops(document *doc) {
    OpList **pp = &op_lists;
    while (*pp) {
        if ((*pp)->doc == doc) {
            OpList *rem = *pp;
            *pp = rem->next;
            Op *op = rem->head;
            while (op) {
                Op *nx = op->next;
                free(op->data);
                free(op);
                op = nx;
            }
            free(rem);
            return;
        }
        pp = &(*pp)->next;
    }
}

// Append an operation
static int enqueue_op(document *doc, Op *op) {
    OpList *lst = get_ops(doc);
    if (!lst)
        return -1;
    op->next = NULL;
    if (lst->tail)
        lst->tail->next = op;
    else
        lst->head = op;
    lst->tail = op;
    return 0;
}

// Get current committed text (caller frees)
static char *get_committed_text(const document *doc) {
    if (!doc->committed_head || !doc->committed_head->data)
        return md_strdup("");
    return md_strdup(doc->committed_head->data);
}

// Apply a single operation to text
static char *apply_single_op(char *text, Op *op) {
    size_t old_len = strlen(text);

    if (op->type == OP_INSERT) {
        size_t pos = op->pos;
        if (pos > old_len)
            pos = old_len;

        size_t data_len = strlen(op->data);
        char *new_text = malloc(old_len + data_len + 1);
        if (!new_text) {
            free(text);
            return NULL;
        }

        memcpy(new_text, text, pos);
        memcpy(new_text + pos, op->data, data_len);
        memcpy(new_text + pos + data_len, text + pos, old_len - pos + 1);

        free(text);
        return new_text;
    } else { // OP_DELETE
        size_t pos = op->pos;
        size_t len = op->len;

        if (pos > old_len)
            pos = old_len;
        if (pos + len > old_len)
            len = old_len - pos;

        char *new_text = malloc(old_len - len + 1);
        if (!new_text) {
            free(text);
            return NULL;
        }

        memcpy(new_text, text, pos);
        memcpy(new_text + pos, text + pos + len, old_len - pos - len + 1);

        free(text);
        return new_text;
    }
}

// Get working text (all operations applied)
static char *get_working_text(const document *doc) {
    char *text = get_committed_text(doc);

    OpList *lst = get_ops((document *)doc);
    if (!lst || !lst->head)
        return text;

    // Apply all operations in order
    for (Op *op = lst->head; op; op = op->next) {
        text = apply_single_op(text, op);
        if (!text)
            return NULL;
    }

    return text;
}

// === Init and Free ===
document *markdown_init(void) {
    document *doc = calloc(1, sizeof(document));
    if (!doc)
        return NULL;
    doc->current_version = 0;

    // Initialise with an empty chunk
    doc->committed_head = malloc(sizeof(chunk));
    if (!doc->committed_head) {
        free(doc);
        return NULL;
    }

    doc->committed_head->data = md_strdup("");
    doc->committed_head->length = 0;
    doc->committed_head->prev = doc->committed_head->next = NULL;
    doc->committed_tail = doc->committed_head;
    doc->committed_chunks = 1;

    // Initialise document fields
    doc->head = doc->tail = NULL;
    doc->n_chunks = 0;

    return doc;
}

void markdown_free(document *doc) {
    if (!doc)
        return;
    // free committed snapshot
    if (doc->committed_head) {
        chunk *current = doc->committed_head;
        while (current) {
            chunk *next = current->next;
            free(current->data);
            free(current);
            current = next;
        }
    }

    // Free document chunks if they exist
    if (doc->head) {
        chunk *current = doc->head;
        while (current) {
            chunk *next = current->next;
            free(current->data);
            free(current);
            current = next;
        }
    }

    // free pending ops
    free_ops(doc);
    free(doc);
}

// === Edit Commands ===
int markdown_insert(document *doc, uint64_t version, size_t pos,
                    const char *content) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;

    // Validate against working text
    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);
    free(working);

    if (pos > n)
        return INVALID_CURSOR_POS;

    Op *op = malloc(sizeof(Op));
    if (!op)
        return -1;
    op->type = OP_INSERT;
    op->pos = pos;
    op->len = 0;
    op->data = md_strdup(content);
    enqueue_op(doc, op);
    return SUCCESS;
}

int markdown_delete(document *doc, uint64_t version, size_t pos, size_t len) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;
    if (len == 0)
        return SUCCESS;

    // Validate against working text
    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);
    free(working);

    if (pos > n || pos + len > n)
        return INVALID_CURSOR_POS;

    Op *op = malloc(sizeof(Op));
    if (!op)
        return -1;
    op->type = OP_DELETE;
    op->pos = pos;
    op->len = len;
    op->data = NULL;
    enqueue_op(doc, op);
    return SUCCESS;
}

// === Formatting Commands ===
int markdown_newline(document *doc, uint64_t version, size_t pos) {
    return markdown_insert(doc, version, pos, "\n");
}

int markdown_heading(document *doc, uint64_t version, size_t level,
                     size_t pos) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;
    if (level < 1 || level > 3)
        return INVALID_CURSOR_POS;

    // Get working state to check for newline
    char *working = get_working_text(doc);
    if (!working)
        return -1;

    // Check if we need newline before
    if (pos > 0 && working[pos - 1] != '\n') {
        free(working);
        int r = markdown_insert(doc, version, pos, "\n");
        if (r != SUCCESS)
            return r;
        pos++;
    } else {
        free(working);
    }

    // Insert hashes + space
    char tag[5] = {0};
    memset(tag, '#', level);
    tag[level] = ' ';
    return markdown_insert(doc, version, pos, tag);
}

int markdown_bold(document *doc, uint64_t version, size_t start, size_t end) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;
    if (start > end)
        return INVALID_CURSOR_POS;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);
    free(working);

    if (end > n)
        return INVALID_CURSOR_POS;

    int r = markdown_insert(doc, version, end, "**");
    if (r != SUCCESS)
        return r;
    return markdown_insert(doc, version, start, "**");
}

int markdown_italic(document *doc, uint64_t version, size_t start, size_t end) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;
    if (start > end)
        return INVALID_CURSOR_POS;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);
    free(working);

    if (end > n)
        return INVALID_CURSOR_POS;

    int r = markdown_insert(doc, version, end, "*");
    if (r != SUCCESS)
        return r;
    return markdown_insert(doc, version, start, "*");
}

int markdown_blockquote(document *doc, uint64_t version, size_t pos) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);

    if (pos > n) {
        free(working);
        return INVALID_CURSOR_POS;
    }

    // Check if we need newline before
    if (pos > 0 && working[pos - 1] != '\n') {
        free(working);
        int r = markdown_insert(doc, version, pos, "\n");
        if (r != SUCCESS)
            return r;
        pos++;
    } else {
        free(working);
    }

    return markdown_insert(doc, version, pos, "> ");
}

int markdown_ordered_list(document *doc, uint64_t version, size_t pos) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);

    if (pos > n) {
        free(working);
        return INVALID_CURSOR_POS;
    }

    int prev = 0;
    // Check if we need newline before
    if (pos > 0 && working[pos - 1] != '\n') {
        free(working);
        int r = markdown_insert(doc, version, pos, "\n");
        if (r != SUCCESS)
            return r;
        pos++;
        // Re-get working state
        working = get_working_text(doc);
        if (!working)
            return -1;
    }

    // Find previous number
    size_t idx = pos;
    while (idx > 0) {
        size_t line_start = idx;
        while (line_start > 0 && working[line_start - 1] != '\n')
            line_start--;

        char *endptr;
        long num = strtol(working + line_start, &endptr, 10);
        if (endptr != working + line_start && *endptr == '.' &&
            *(endptr + 1) == ' ') {
            prev = (int)num;
            break;
        }

        if (line_start == 0)
            break;
        idx = line_start - 1;
    }
    free(working);

    char prefix[32];
    snprintf(prefix, sizeof(prefix), "%d. ", prev + 1);
    return markdown_insert(doc, version, pos, prefix);
}

int markdown_unordered_list(document *doc, uint64_t version, size_t pos) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);

    if (pos > n) {
        free(working);
        return INVALID_CURSOR_POS;
    }

    // Check if we need newline before
    if (pos > 0 && working[pos - 1] != '\n') {
        free(working);
        int r = markdown_insert(doc, version, pos, "\n");
        if (r != SUCCESS)
            return r;
        pos++;
    } else {
        free(working);
    }

    return markdown_insert(doc, version, pos, "- ");
}

int markdown_code(document *doc, uint64_t version, size_t start, size_t end) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;
    if (start > end)
        return INVALID_CURSOR_POS;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);
    free(working);

    if (end > n)
        return INVALID_CURSOR_POS;

    int r = markdown_insert(doc, version, end, "`");
    if (r != SUCCESS)
        return r;
    return markdown_insert(doc, version, start, "`");
}

int markdown_horizontal_rule(document *doc, uint64_t version, size_t pos) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);

    if (pos > n) {
        free(working);
        return INVALID_CURSOR_POS;
    }

    // Check if we need newline before
    if (pos > 0 && working[pos - 1] != '\n') {
        free(working);
        int r = markdown_insert(doc, version, pos, "\n");
        if (r != SUCCESS)
            return r;
        pos++;
    } else {
        free(working);
    }

    return markdown_insert(doc, version, pos, "---\n");
}

int markdown_link(document *doc, uint64_t version, size_t start, size_t end,
                  const char *url) {
    if (!doc)
        return INVALID_CURSOR_POS;
    if (version != doc->current_version)
        return OUTDATED_VERSION;
    if (!url)
        return INVALID_CURSOR_POS;
    if (start > end)
        return INVALID_CURSOR_POS;

    char *working = get_working_text(doc);
    if (!working)
        return -1;
    size_t n = strlen(working);
    free(working);

    if (end > n)
        return INVALID_CURSOR_POS;

    int r = markdown_insert(doc, version, end, ")");
    if (r != SUCCESS)
        return r;
    r = markdown_insert(doc, version, end, url);
    if (r != SUCCESS)
        return r;
    r = markdown_insert(doc, version, end, "(");
    if (r != SUCCESS)
        return r;
    r = markdown_insert(doc, version, end, "]");
    if (r != SUCCESS)
        return r;
    return markdown_insert(doc, version, start, "[");
}

// === Utilities ===
void markdown_print(const document *doc, FILE *stream) {
    if (!doc || !stream)
        return;
    char *txt = markdown_flatten(doc);
    if (txt) {
        fputs(txt, stream);
        free(txt);
    }
}

char *markdown_flatten(const document *doc) {
    if (!doc)
        return NULL;
    // Return only committed text
    return get_committed_text(doc);
}

// === Versioning ===
void markdown_increment_version(document *doc) {
    if (!doc)
        return;

    // Increment version first
    doc->current_version++;

    // Get working text
    char *new_text = get_working_text(doc);
    if (!new_text)
        return;

    // Commit the new text
    if (doc->committed_head) {
        free(doc->committed_head->data);
    } else {
        doc->committed_head = doc->committed_tail = malloc(sizeof(chunk));
        if (!doc->committed_head) {
            free(new_text);
            return;
        }
        doc->committed_head->prev = doc->committed_head->next = NULL;
        doc->committed_chunks = 1;
    }

    doc->committed_head->data = new_text;
    doc->committed_head->length = strlen(new_text);

    // Clear pending operations
    OpList *lst = get_ops(doc);
    if (lst) {
        Op *op = lst->head;
        while (op) {
            Op *nx = op->next;
            free(op->data);
            free(op);
            op = nx;
        }
        lst->head = lst->tail = NULL;
    }
}