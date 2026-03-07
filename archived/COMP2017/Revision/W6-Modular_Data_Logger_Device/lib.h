#ifndef WEEK6_LIB_H
#define WEEK6_LIB_H

#include <stddef.h> // For size_t



// --- Data Record Definition ---
typedef struct
{
    int id;
    double value;
    long timestamp;
} DataRecord;

// Forward declaration for device struct
typedef struct DataLoggerDevice DataLoggerDevice;

// --- Function Pointer Typedefs ---
typedef int (*DeviceOpenFunc)(DataLoggerDevice *dev);
typedef int (*DeviceWriteFunc)(DataLoggerDevice *dev, const DataRecord *record);
typedef int (*DeviceReadFunc)(DataLoggerDevice *dev, DataRecord *buf, size_t n_records);
typedef int (*DeviceSortFunc)(DataLoggerDevice *dev, int (*cmp)(const void *, const void *));
typedef int (*DeviceCloseFunc)(DataLoggerDevice *dev);

// --- Device Struct ---
struct DataLoggerDevice
{
    DeviceOpenFunc open;
    DeviceWriteFunc write;
    DeviceReadFunc read;
    DeviceSortFunc sort;
    DeviceCloseFunc close;
    void *state; // Opaque pointer to device-specific state
};

// --- API Prototypes ---
int device_open(DataLoggerDevice *dev);
int device_write(DataLoggerDevice *dev, const DataRecord *record);
int device_read(DataLoggerDevice *dev, DataRecord *buf, size_t n_records);
int device_sort(DataLoggerDevice *dev, int (*cmp)(const void *, const void *));
int device_close(DataLoggerDevice *dev);

#endif // WEEK6_LIB_H

