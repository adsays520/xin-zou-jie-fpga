#pragma once
#define O_RDONLY 0
#define O_NONBLOCK 0x800
int open(const char *path, int flags, ...);
