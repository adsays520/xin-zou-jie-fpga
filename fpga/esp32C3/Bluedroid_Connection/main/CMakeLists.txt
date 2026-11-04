idf_component_register(
    SRCS "main.c" "cy8cmbr3116.c" "touch_serial.c" "touch_layout.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES esp_driver_i2c esp_driver_uart
)
