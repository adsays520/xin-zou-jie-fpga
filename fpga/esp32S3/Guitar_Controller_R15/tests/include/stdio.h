#ifndef TEST_STDIO_H
#define TEST_STDIO_H
#include <stddef.h>
#include <stdarg.h>
int snprintf(char *buffer, size_t size, const char *format, ...);
int vsnprintf(char *buffer, size_t size, const char *format, va_list arguments);
int sscanf(const char *text, const char *format, ...);
/* Opaque mock stream, only passed to the GPIO dump stub, never dereferenced. */
typedef struct test_stdio_stream FILE;
#define stdout ((FILE *)1)
#endif
