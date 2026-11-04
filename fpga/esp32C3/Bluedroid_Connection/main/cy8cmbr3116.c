#include "cy8cmbr3116.h"
#include "touch_board.h"

#include <stddef.h>

#include "driver/i2c_master.h"

#define CY8_I2C_SDA_GPIO        TOUCH_SDA_GPIO
#define CY8_I2C_SCL_GPIO        TOUCH_SCL_GPIO
#define CY8_I2C_FREQUENCY_HZ    100000
#define CY8_I2C_TIMEOUT_MS      100
#define CY8_REG_SENSOR_EN       0x00
#define CY8_REG_DEVICE_ID       0x90
#define CY8_REG_BUTTON_STAT     0xAA
#define CY8_REG_DIFF_COUNT_0    0xBA
#define CY8_DEVICE_ID_3116     0x0A05

static const uint8_t s_addresses[CY8_DEVICE_COUNT] = {
    0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E,
};
static i2c_master_bus_handle_t s_bus;
static i2c_master_dev_handle_t s_devices[CY8_DEVICE_COUNT];

uint8_t cy8cmbr3116_address(uint8_t chip)
{
    return chip < CY8_DEVICE_COUNT ? s_addresses[chip] : 0;
}

esp_err_t cy8cmbr3116_init(void)
{
    if (s_bus != NULL) {
        return ESP_OK;
    }

    const i2c_master_bus_config_t bus_config = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = CY8_I2C_SDA_GPIO,
        .scl_io_num = CY8_I2C_SCL_GPIO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t err = i2c_new_master_bus(&bus_config, &s_bus);
    if (err != ESP_OK) {
        return err;
    }

    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        const i2c_device_config_t device_config = {
            .dev_addr_length = I2C_ADDR_BIT_LEN_7,
            .device_address = s_addresses[chip],
            .scl_speed_hz = CY8_I2C_FREQUENCY_HZ,
        };
        err = i2c_master_bus_add_device(s_bus, &device_config, &s_devices[chip]);
        if (err != ESP_OK) {
            for (uint8_t j = 0; j < chip; ++j) {
                i2c_master_bus_rm_device(s_devices[j]);
                s_devices[j] = NULL;
            }
            i2c_del_master_bus(s_bus);
            s_bus = NULL;
            return err;
        }
    }
    return ESP_OK;
}

static esp_err_t cy8_read(uint8_t chip, uint8_t reg, uint8_t *data, size_t length)
{
    if (chip >= CY8_DEVICE_COUNT || data == NULL || length == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    if (s_devices[chip] == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit_receive(s_devices[chip], &reg, 1, data, length,
                                       CY8_I2C_TIMEOUT_MS);
}

static esp_err_t cy8_read_u16(uint8_t chip, uint8_t reg, uint16_t *value)
{
    if (value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    uint8_t bytes[2];
    esp_err_t err = cy8_read(chip, reg, bytes, sizeof(bytes));
    if (err == ESP_OK) {
        *value = (uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8);
    }
    return err;
}

esp_err_t cy8cmbr3116_verify(uint8_t chip, uint16_t *sensor_enable)
{
    if (sensor_enable == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    uint16_t device_id;
    esp_err_t err = cy8_read_u16(chip, CY8_REG_DEVICE_ID, &device_id);
    if (err != ESP_OK) {
        return err;
    }
    if (device_id != CY8_DEVICE_ID_3116) {
        return ESP_ERR_INVALID_RESPONSE;
    }
    return cy8_read_u16(chip, CY8_REG_SENSOR_EN, sensor_enable);
}

esp_err_t cy8cmbr3116_read_buttons(uint8_t chip, uint16_t *button_state)
{
    return cy8_read_u16(chip, CY8_REG_BUTTON_STAT, button_state);
}

esp_err_t cy8cmbr3116_read_difference_counts(uint8_t chip,
                                               uint16_t counts[CY8_CHANNEL_COUNT])
{
    if (counts == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    for (uint8_t channel = 0; channel < CY8_CHANNEL_COUNT; ++channel) {
        esp_err_t err = cy8_read_u16(chip,
                                     (uint8_t)(CY8_REG_DIFF_COUNT_0 + 2U * channel),
                                     &counts[channel]);
        if (err != ESP_OK) {
            return err;
        }
    }
    return ESP_OK;
}
