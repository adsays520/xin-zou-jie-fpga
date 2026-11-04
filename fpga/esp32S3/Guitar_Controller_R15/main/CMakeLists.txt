set(TOUCH_SOURCE "${CMAKE_CURRENT_LIST_DIR}/../../../esp32C3/Bluedroid_Connection/main")
idf_component_register(
    SRCS "main.c" "ble_control.c" "led_logic.c" "led_indicator.c" "led_frame_encoder.c" "led_frame_check.c" "led_probe.c" "fpga_link.c" "fpga_protocol.c" "fpga_scheduler.c" "hall_detector.c" "hall_adc.c" "host_usb.c" "control_line.c"
         "cy8cmbr3116.c"
         "${TOUCH_SOURCE}/touch_layout.c"
         "touch_serial.c" "touch_output.c" "note_trace.c"
    INCLUDE_DIRS "." "${TOUCH_SOURCE}"
    PRIV_REQUIRES bt nvs_flash esp_driver_rmt esp_driver_i2c esp_driver_uart esp_driver_spi esp_driver_gpio esp_driver_usb_serial_jtag esp_hw_support esp_adc esp_timer
)
