#pragma once
#include "idf_test.h"
typedef void *adc_oneshot_unit_handle_t;
typedef int adc_channel_t;
typedef struct {int unit_id;} adc_oneshot_unit_init_cfg_t;
typedef struct {int atten; int bitwidth;} adc_oneshot_chan_cfg_t;
#define ADC_UNIT_1 1
#define ADC_UNIT_2 2
#define ADC_CHANNEL_0 0
#define ADC_CHANNEL_1 1
#define ADC_CHANNEL_3 3
#define ADC_CHANNEL_4 4
#define ADC_CHANNEL_5 5
#define ADC_CHANNEL_6 6
#define ADC_CHANNEL_7 7
#define ADC_ATTEN_DB_12 12
#define ADC_BITWIDTH_12 12
esp_err_t adc_oneshot_new_unit(const adc_oneshot_unit_init_cfg_t *config, adc_oneshot_unit_handle_t *handle);
esp_err_t adc_oneshot_config_channel(adc_oneshot_unit_handle_t handle, adc_channel_t channel, const adc_oneshot_chan_cfg_t *config);
esp_err_t adc_oneshot_read(adc_oneshot_unit_handle_t handle, adc_channel_t channel, int *raw);
esp_err_t adc_oneshot_del_unit(adc_oneshot_unit_handle_t handle);
