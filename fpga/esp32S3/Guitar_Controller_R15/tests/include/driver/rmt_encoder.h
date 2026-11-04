#ifndef LED_TEST_RMT_ENCODER_H
#define LED_TEST_RMT_ENCODER_H
#include "idf_test.h"
typedef void *rmt_channel_handle_t;
typedef union {
    struct {uint32_t duration0:15,level0:1,duration1:15,level1:1;};
    uint32_t val;
} rmt_symbol_word_t;
typedef unsigned rmt_encode_state_t;
#define RMT_ENCODING_RESET 0
#define RMT_ENCODING_COMPLETE 1
#define RMT_ENCODING_MEM_FULL 2
#define RMT_ENCODER_FUNC_ATTR
typedef struct rmt_encoder_t rmt_encoder_t;
struct rmt_encoder_t {
    size_t (*encode)(rmt_encoder_t *,rmt_channel_handle_t,const void *,size_t,rmt_encode_state_t *);
    esp_err_t (*reset)(rmt_encoder_t *);
    esp_err_t (*del)(rmt_encoder_t *);
};
typedef rmt_encoder_t *rmt_encoder_handle_t;
typedef struct {rmt_symbol_word_t bit0,bit1;struct {unsigned msb_first:1;} flags;} rmt_bytes_encoder_config_t;
typedef struct {int unused;} rmt_copy_encoder_config_t;
esp_err_t rmt_new_copy_encoder(const rmt_copy_encoder_config_t *, rmt_encoder_handle_t *);
esp_err_t rmt_del_encoder(rmt_encoder_handle_t);
esp_err_t rmt_encoder_reset(rmt_encoder_handle_t);
esp_err_t rmt_new_bytes_encoder(const rmt_bytes_encoder_config_t *,rmt_encoder_handle_t *);
void *rmt_alloc_encoder_mem(size_t size);
#endif
