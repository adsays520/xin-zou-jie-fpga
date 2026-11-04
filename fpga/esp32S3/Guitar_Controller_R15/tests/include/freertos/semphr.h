#pragma once
#include "idf_test.h"
typedef void *SemaphoreHandle_t;
SemaphoreHandle_t xSemaphoreCreateMutex(void);
SemaphoreHandle_t xSemaphoreCreateBinary(void);
int xSemaphoreTake(SemaphoreHandle_t handle,TickType_t wait);
int xSemaphoreGive(SemaphoreHandle_t handle);
