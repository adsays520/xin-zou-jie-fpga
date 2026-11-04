#ifndef LED_TEST_RMT_RX_H
#define LED_TEST_RMT_RX_H
#include "driver/rmt_tx.h"
typedef struct {rmt_symbol_word_t *received_symbols;size_t num_symbols;} rmt_rx_done_event_data_t;
typedef bool (*rmt_rx_done_callback_t)(rmt_channel_handle_t,const rmt_rx_done_event_data_t *,void *);
typedef struct {rmt_rx_done_callback_t on_recv_done;} rmt_rx_event_callbacks_t;
typedef struct {int gpio_num,clk_src;uint32_t resolution_hz;size_t mem_block_symbols;struct {unsigned with_dma:1;} flags;} rmt_rx_channel_config_t;
typedef struct {uint32_t signal_range_min_ns,signal_range_max_ns;} rmt_receive_config_t;
esp_err_t rmt_new_rx_channel(const rmt_rx_channel_config_t *,rmt_channel_handle_t *);
esp_err_t rmt_rx_register_event_callbacks(rmt_channel_handle_t,const rmt_rx_event_callbacks_t *,void *);
esp_err_t rmt_receive(rmt_channel_handle_t,void *,size_t,const rmt_receive_config_t *);
#endif
