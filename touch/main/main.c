#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/usb_serial_jtag.h"
#include "driver/usb_serial_jtag_vfs.h"
#include "esp_err.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define CONFIG_SDA_GPIO 5
#define CONFIG_SCL_GPIO 4
#define CONFIG_BLOCK_SIZE 16
#define CONFIG_ARM_US 30000000

static i2c_master_dev_handle_t s_devices[8];
static int64_t s_armed_until_us;

static unsigned bus_lines(void)
{
    return (unsigned)((gpio_get_level(CONFIG_SDA_GPIO) << 1) |
                       gpio_get_level(CONFIG_SCL_GPIO));
}

static i2c_master_dev_handle_t device_for(unsigned address)
{
    if (address < 0x37 || address > 0x3E) return NULL;
    return s_devices[address - 0x37];
}

static void reply_error(unsigned sequence, esp_err_t err, unsigned before,
                        unsigned after, int64_t elapsed_us)
{
    printf("ERR,%u,%X,%u,%u,%lld\n", sequence, (unsigned)err,
           before, after, (long long)elapsed_us);
    fflush(stdout);
}

static void execute_line(const char *line)
{
    unsigned sequence = 0;
    unsigned address = 0;
    unsigned reg = 0;
    unsigned length = 0;
    char extra;
    if (sscanf(line, "PING,%u%c", &sequence, &extra) == 1) {
        printf("PONG,%u,CY8CFG1\n", sequence);
        fflush(stdout);
        return;
    }
    char token[16];
    if (sscanf(line, "ARM,%u,%15s", &sequence, token) == 2 && strcmp(token, "CY8CFG1") == 0) {
        s_armed_until_us = esp_timer_get_time() + CONFIG_ARM_US;
        printf("OK,%u,ARMED\n", sequence);
        fflush(stdout);
        return;
    }
    if (sscanf(line, "LOCK,%u%c", &sequence, &extra) == 1) {
        s_armed_until_us = 0;
        printf("OK,%u,LOCKED\n", sequence);
        fflush(stdout);
        return;
    }
    bool reading = sscanf(line, "R,%u,%x,%x,%u%c", &sequence, &address,
                           &reg, &length, &extra) == 4;
    uint8_t data[CONFIG_BLOCK_SIZE + 1];
    if (!reading) {
        char payload[CONFIG_BLOCK_SIZE * 2 + 1];
        if (sscanf(line, "W,%u,%x,%x,%32[0123456789abcdefABCDEF]%c",
                   &sequence, &address, &reg, payload, &extra) != 4 ||
            strlen(payload) % 2 != 0) {
            reply_error(sequence, ESP_ERR_INVALID_ARG, bus_lines(), bus_lines(), 0);
            return;
        }
        length = strlen(payload) / 2;
        for (unsigned index = 0; index < length; ++index) {
            char byte_text[3] = {payload[index * 2], payload[index * 2 + 1], 0};
            data[index + 1] = (uint8_t)strtoul(byte_text, NULL, 16);
        }
    }
    i2c_master_dev_handle_t device = device_for(address);
    bool allowed_range = reading || (reg < 128 && length <= 128 - reg) ||
                         (reg == 0x86 && length == 1 && (data[1] == 2 || data[1] == 255));
    if (device == NULL || length == 0 || length > CONFIG_BLOCK_SIZE || reg > 255 ||
        length > 256 - reg || !allowed_range) {
        reply_error(sequence, ESP_ERR_INVALID_ARG, bus_lines(), bus_lines(), 0);
        return;
    }
    if (!reading && esp_timer_get_time() >= s_armed_until_us) {
        reply_error(sequence, ESP_ERR_INVALID_STATE, bus_lines(), bus_lines(), 0);
        return;
    }
    unsigned before = bus_lines();
    int64_t start_us = esp_timer_get_time();
    data[0] = (uint8_t)reg;
    esp_err_t err;
    if (reading) {
        err = i2c_master_transmit_receive(device, data, 1, data + 1, length, 10);
    } else {
        err = i2c_master_transmit(device, data, length + 1, 10);
    }
    int64_t elapsed_us = esp_timer_get_time() - start_us;
    unsigned after = bus_lines();
    if (err != ESP_OK) {
        reply_error(sequence, err, before, after, elapsed_us);
        return;
    }
    printf("OK,%u,", sequence);
    if (reading) {
        for (unsigned index = 0; index < length; ++index) printf("%02X", data[index + 1]);
    } else {
        printf("WRITTEN");
    }
    printf("\n");
    fflush(stdout);
}

void app_main(void)
{
    usb_serial_jtag_driver_config_t usb_config = {
        .tx_buffer_size = 2048,
        .rx_buffer_size = 512,
    };
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb_config));
    usb_serial_jtag_vfs_use_driver();
    i2c_master_bus_handle_t bus;
    const i2c_master_bus_config_t bus_config = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = CONFIG_SDA_GPIO,
        .scl_io_num = CONFIG_SCL_GPIO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_config, &bus));
    for (unsigned chip = 0; chip < 8; ++chip) {
        const i2c_device_config_t device_config = {
            .dev_addr_length = I2C_ADDR_BIT_LEN_7,
            .device_address = 0x37 + chip,
            .scl_speed_hz = 100000,
        };
        ESP_ERROR_CHECK(i2c_master_bus_add_device(bus, &device_config, &s_devices[chip]));
    }
    ESP_LOGI("CY8_CONFIG", "CY8CFG1: USB command bridge only; SDA=5 SCL=4 100kHz; all eight addresses enabled; writes LOCKED");
    char line[96];
    size_t used = 0;
    bool overflow = false;
    for (;;) {
        uint8_t byte;
        if (usb_serial_jtag_read_bytes(&byte, 1, pdMS_TO_TICKS(100)) != 1) continue;
        if (byte == '\r' || byte == '\n') {
            if (used != 0 && !overflow) {
                line[used] = '\0';
                execute_line(line);
            }
            used = 0;
            overflow = false;
        } else if (!overflow && used < sizeof(line) - 1) {
            line[used++] = (char)byte;
        } else {
            overflow = true;
        }
    }
}
