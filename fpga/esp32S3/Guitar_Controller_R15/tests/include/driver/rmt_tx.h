#ifndef LED_TEST_RMT_TX_H
#define LED_TEST_RMT_TX_H
#include "driver/rmt_encoder.h"
typedef struct {int gpio_num,clk_src;uint32_t resolution_hz;size_t mem_block_symbols,trans_queue_depth;struct {unsigned with_dma:1;} flags;} rmt_tx_channel_config_t;
typedef struct {int loop_count;} rmt_transmit_config_t;
#define RMT_CLK_SRC_DEFAULT 0
esp_err_t rmt_new_tx_channel(const rmt_tx_channel_config_t *, rmt_channel_handle_t *);
esp_err_t rmt_enable(rmt_channel_handle_t);
esp_err_t rmt_tx_switch_gpio(rmt_channel_handle_t,int,bool);
esp_err_t rmt_disable(rmt_channel_handle_t);
esp_err_t rmt_del_channel(rmt_channel_handle_t);
esp_err_t rmt_transmit(rmt_channel_handle_t,rmt_encoder_handle_t,const void *,size_t,const rmt_transmit_config_t *);
esp_err_t rmt_tx_wait_all_done(rmt_channel_handle_t,int);
void vTaskDelete(void *);
#endif
