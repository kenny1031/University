#include "lib.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>


typedef struct {
    DataRecord *buf;
    size_t len;
    size_t capacity;
} MemoryState;

// --- API Prototypes from lib.h---
int device_open(DataLoggerDevice *dev) {
    if (!dev || !dev->open) return -1;
    return dev->open(dev);
}

int device_write(DataLoggerDevice *dev, const DataRecord *record) {
    if (!dev || !record || !dev->write) return -1;
    return dev->write(dev, record);
}

int device_read(DataLoggerDevice *dev, DataRecord *buf, size_t n_records) {
    if (!dev || !dev->read || !buf) return -1;
    return dev->read(dev, buf, n_records);
}

int device_sort(DataLoggerDevice *dev, int (*cmp)(const void *, const void *)) {
    if (!dev || !dev->sort || !cmp) return -1;
    return dev->sort(dev, cmp);
}

int device_close(DataLoggerDevice *dev) {
    if (!dev || !dev->close) return -1;
    return dev->close(dev);
}

// Callback functions
static int mem_open(DataLoggerDevice *dev) {
    if (!dev) return -1;
    MemoryState *st = malloc(sizeof *st);
    if (!st) return -1;

    st->buf = NULL;
    st->capacity = st->len = 0;

    dev->state = st;
    return 0;
}

static int mem_write(DataLoggerDevice *dev, const DataRecord *rec)
{
    if (!dev || !rec) return -1;
    MemoryState *st = dev->state;
    if (!st) return -1;

    if (st->len == st->capacity) {
        /* choose next capacity and check for SIZE_MAX overflow      */
        size_t new_cap = st->capacity ? st->capacity * 2 : 8;
        if (new_cap > SIZE_MAX / sizeof *st->buf) return -1;

        DataRecord *tmp = realloc(st->buf, new_cap * sizeof *tmp);
        if (!tmp) return -1;          /* leave state unchanged      */
        st->buf = tmp;
        st->capacity = new_cap;
    }

    st->buf[st->len++] = *rec;        /* safe struct copy            */
    return 0;
}

static int mem_read(DataLoggerDevice *dev, DataRecord *buf, size_t n_records) {
    if (!dev || !buf) return -1;
    MemoryState *state = dev->state;
    if (!state) return -1;

    if (n_records > state->len) n_records = state->len;
    memcpy(buf, state->buf, n_records * sizeof(DataRecord));
    return (int)n_records;
}

static int mem_sort(DataLoggerDevice *dev, int (*cmp)(const void *, const void *)) {
    if (!dev || !cmp) return -1;
    MemoryState *st = dev->state;
    if (!st) return -1;

    /* nothing to do for 0 or 1 element – avoid qsort(NULL, 0, …)    */
    if (st->len > 1)
        qsort(st->buf, st->len, sizeof *st->buf, cmp);

    return 0;
}

static int mem_close(DataLoggerDevice *dev) {
    if (!dev) return -1;
    MemoryState *state = dev->state;
    if (state) {
        free(state->buf);
        free(state);
    }
    dev->state = NULL;
    return 0;
}

DataLoggerDevice *create_memory_device(void) {
    DataLoggerDevice *device = calloc(1, sizeof(sizeof(DataLoggerDevice)));
    if (!device) return NULL;
    device->open = mem_open;
    device->write = mem_write;
    device->read = mem_read;
    device->sort = mem_sort;
    device->close = mem_close;
    return device;
}