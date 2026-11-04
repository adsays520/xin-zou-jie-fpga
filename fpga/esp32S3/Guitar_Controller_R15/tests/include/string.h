#pragma once
#include <stddef.h>
void *memset(void *destination, int value, size_t length);
void *memcpy(void *destination, const void *source, size_t length);
size_t strlen(const char *text);
int strcmp(const char *first, const char *second);
int strncmp(const char *first, const char *second, size_t length);
