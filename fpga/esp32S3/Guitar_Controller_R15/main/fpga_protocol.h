#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define FPGA_FRAME_SIZE 64U
#define FPGA_PROTOCOL_VERSION 1U
#define FPGA_HALL_SNAPSHOT_TAG 0xC1U
uint16_t fpga_crc16(const uint8_t *data, size_t length);
bool fpga_fixed_command_valid(const uint8_t command[6]);
void fpga_frame_build(uint8_t frame[64], uint32_t session, uint16_t sequence,
                     uint8_t online, const uint8_t keys[16], const uint8_t *command);
void fpga_frame_attach_pick(uint8_t frame[64], uint8_t string_number, uint8_t velocity, const uint8_t keys[16]);
bool fpga_command_slot_ready(const uint8_t reply[64]);
bool fpga_hall_slot_ready(const uint8_t reply[64]);
bool fpga_reply_valid(const uint8_t frame[64]);
uint32_t fpga_frame_session(const uint8_t frame[64]);
uint16_t fpga_frame_sequence(const uint8_t frame[64]);
