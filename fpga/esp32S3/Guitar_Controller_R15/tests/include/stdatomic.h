#ifndef TOUCH_TEST_STDATOMIC_H
#define TOUCH_TEST_STDATOMIC_H
#include <stdbool.h>
#define _Atomic volatile
#define atomic_load(value) (*(value))
#define atomic_store(value, replacement) (*(value) = (replacement))
static inline bool test_atomic_compare_unsigned(volatile unsigned *value, unsigned *expected, unsigned replacement)
{
    if (*value == *expected) {*value = replacement; return true;}
    *expected = *value; return false;
}
#define atomic_compare_exchange_strong(value, expected, replacement) test_atomic_compare_unsigned(value, expected, replacement)
static inline bool test_atomic_exchange(volatile bool *value, bool replacement)
{
    bool previous = *value;
    *value = replacement;
    return previous;
}
#define atomic_exchange(value, replacement) test_atomic_exchange(value, replacement)
static inline unsigned test_atomic_fetch_add(volatile unsigned *value, unsigned increment)
{
    unsigned previous = *value;
    *value += increment;
    return previous;
}
#define atomic_fetch_add(value, increment) test_atomic_fetch_add(value, increment)
#endif
