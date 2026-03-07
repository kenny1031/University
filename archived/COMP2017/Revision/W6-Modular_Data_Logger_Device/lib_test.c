#include <assert.h>
#include "lib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define ASSERT_OK(expr)   assert((expr) == 0)
#define ASSERT_ERR(expr)  assert((expr) == -1)

extern DataLoggerDevice *create_memory_device(void);

int cmp_by_timestamp(const void *a, const void *b) {
    long t1 = ((const DataRecord *)a)->timestamp;
    long t2 = ((const DataRecord *)b)->timestamp;
    return (t1 > t2) - (t1 < t2);
}

int cmp_by_value_desc(const void *a, const void *b) {
    double v1 = ((const DataRecord *)a)->value;
    double v2 = ((const DataRecord *)b)->value;
    return (v1 < v2) - (v1 > v2);   // descending
}

static void test_sort_edge_cases(void)
{
    /* ---------- empty device ---------- */
    DataLoggerDevice *dev = create_memory_device();
    ASSERT_OK(device_open(dev));
    ASSERT_OK(device_sort(dev, cmp_by_timestamp));   // no records → no crash
    DataRecord dummy;
    assert(device_read(dev, &dummy, 1) == 0);
    ASSERT_OK(device_close(dev));
    free(dev);

    /* ---------- single record ---------- */
    dev = create_memory_device();
    ASSERT_OK(device_open(dev));
    DataRecord r = { .id = 1, .value = 10.0, .timestamp = 5 };
    ASSERT_OK(device_write(dev, &r));
    ASSERT_OK(device_sort(dev, cmp_by_timestamp));
    DataRecord out;
    assert(device_read(dev, &out, 1) == 1);
    assert(out.timestamp == 5);
    ASSERT_OK(device_close(dev));
    free(dev);

    /* ---------- many random records ---------- */
    const size_t N = 1000;
    dev = create_memory_device();
    ASSERT_OK(device_open(dev));

    srand((unsigned)time(NULL));
    for (size_t i = 0; i < N; ++i) {
        DataRecord rec = {
            .id        = (int)i,
            .value     = rand() / (double)RAND_MAX,
            .timestamp = rand() % 1000000
        };
        ASSERT_OK(device_write(dev, &rec));
    }
    ASSERT_OK(device_sort(dev, cmp_by_timestamp));

    /* verify monotone non-decreasing timestamps */
    DataRecord *buf = malloc(N * sizeof *buf);
    assert(device_read(dev, buf, N) == (int)N);
    for (size_t i = 1; i < N; ++i)
        assert(buf[i-1].timestamp <= buf[i].timestamp);
    free(buf);

    /* resort descending by value and check */
    ASSERT_OK(device_sort(dev, cmp_by_value_desc));
    buf = malloc(N * sizeof *buf);
    assert(device_read(dev, buf, N) == (int)N);
    for (size_t i = 1; i < N; ++i)
        assert(buf[i-1].value >= buf[i].value);
    free(buf);

    ASSERT_OK(device_close(dev));
    free(dev);
}

static void test_close_semantics(void)
{
    DataLoggerDevice *dev = create_memory_device();
    ASSERT_OK(device_open(dev));

    DataRecord rec = { .id = 99, .value = 1.23, .timestamp = 999 };
    ASSERT_OK(device_write(dev, &rec));
    ASSERT_OK(device_close(dev));     // first close succeeds

    /* operations after close must fail */
    ASSERT_ERR(device_write(dev, &rec));
    ASSERT_ERR(device_read(dev, &rec, 1));
    ASSERT_ERR(device_sort(dev, cmp_by_timestamp));

    /* second close should **not** seg-fault, but return error */
    ASSERT_ERR(device_close(dev));

    free(dev);
}

int main() {
    DataLoggerDevice *dev = create_memory_device();
    assert(dev);
    assert(device_open(dev) == 0);

    DataRecord r1 = {
        .id = 42,
        .value = 3.14,
        .timestamp = 100
    };

    DataRecord r2 = {
        .id = 43,
        .value = 2.71,
        .timestamp = 50
    };
    assert(device_write(dev, &r1) == 0);
    assert(device_write(dev, &r2) == 0);

    DataRecord out[2];
    int n = device_read(dev, out, 2);
    assert(n == 2);
    assert(out[0].timestamp == 100);
    assert(out[1].timestamp == 50);

    assert(device_close(dev) == 0);
    free(dev);
    return 0;

}
