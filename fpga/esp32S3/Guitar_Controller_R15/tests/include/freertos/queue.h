#pragma once
#include "idf_test.h"
#define pdTRUE 1
#define pdFALSE 0
#define portMAX_DELAY UINT32_MAX
typedef struct sim_queue *QueueHandle_t;
QueueHandle_t xQueueCreate(unsigned length, unsigned item_size);
int xQueueSend(QueueHandle_t queue, const void *item, TickType_t wait);
int xQueueReceive(QueueHandle_t queue, void *item, TickType_t wait);
int xQueuePeek(QueueHandle_t queue, void *item, TickType_t wait);
unsigned uxQueueMessagesWaiting(QueueHandle_t queue);
