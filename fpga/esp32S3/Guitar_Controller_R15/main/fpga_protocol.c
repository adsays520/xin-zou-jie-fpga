#include "fpga_protocol.h"
#include <string.h>

uint16_t fpga_crc16(const uint8_t *data, size_t length)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (unsigned b = 0; b < 8; ++b) {
            crc = crc & 0x8000U ? (uint16_t)((crc << 1) ^ 0x1021U) : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

bool fpga_fixed_command_valid(const uint8_t command[6])
{
    uint8_t checksum = 0;
    for (unsigned i = 0; i < 6; ++i) checksum ^= command[i];
    if (command[0] != 0xA5 || checksum != 0) return false;
    /* Variable-sized upload frames 0x11/0x21/0x31 and multi-packet uploads
     * stay on the existing PC UART. This link accepts atomic fixed controls. */
    uint8_t c = command[1];
    return (c >= 0x02 && c <= 0x06) || c == 0x08 || c == 0x09 || c == 0x23 || c == 0x24 ||
           (c >= 0x40 && c <= 0x44) || (c >= 0x50 && c <= 0x52) ||
           c == 0x90 || c == 0x91 || c == 0x56 || c == 0x57 || (c >= 0x60 && c <= 0x62) || c == 0x70;
}

void fpga_frame_build(uint8_t frame[64], uint32_t session, uint16_t sequence,
                     uint8_t online, const uint8_t keys[16], const uint8_t *command)
{
    memset(frame, 0, FPGA_FRAME_SIZE);
    frame[0] = 0xA5; frame[1] = 0x53; frame[2] = FPGA_PROTOCOL_VERSION;
    frame[3] = command != NULL ? 1 : 0;
    frame[4] = (uint8_t)sequence; frame[5] = (uint8_t)(sequence >> 8);
    frame[6] = online; frame[7] = command != NULL ? 6 : 16;
    memcpy(frame + 8, keys, 16);
    frame[23] &= 0x3F;
    if (command != NULL) memcpy(frame + 24, command, 6);
    for (unsigned i = 0; i < 4; ++i) frame[56 + i] = (uint8_t)(session >> (8U * i));
    uint16_t crc = fpga_crc16(frame, 62);
    frame[62] = (uint8_t)(crc >> 8); frame[63] = (uint8_t)crc;
}

void fpga_frame_attach_pick(uint8_t frame[64], uint8_t string_number, uint8_t velocity, const uint8_t keys[16])
{
    frame[3] = 2;
    frame[7] = 7;
    memset(frame + 31, 0, 7);
    frame[31] = (uint8_t)(1U << (6U - string_number));
    frame[32 + 6U - string_number] = velocity;
    frame[38] = FPGA_HALL_SNAPSHOT_TAG;
    memcpy(frame + 40, keys, 16);
    frame[55] &= 0x3F;
}

bool fpga_command_slot_ready(const uint8_t reply[64])
{
    return (reply[3] & 2U) != 0;
}

bool fpga_hall_slot_ready(const uint8_t reply[64])
{
    return reply[46] != FPGA_HALL_SNAPSHOT_TAG || (reply[47] & 2U) != 0;
}

bool fpga_reply_valid(const uint8_t frame[64])
{
    return frame[0] == 0x5A && frame[1] == 0x53 && frame[2] == FPGA_PROTOCOL_VERSION &&
           (frame[3] & 1U) != 0 &&
           fpga_crc16(frame, 62) == ((uint16_t)frame[62] << 8 | frame[63]);
}

uint32_t fpga_frame_session(const uint8_t frame[64])
{
    return (uint32_t)frame[56] | (uint32_t)frame[57] << 8 |
           (uint32_t)frame[58] << 16 | (uint32_t)frame[59] << 24;
}

uint16_t fpga_frame_sequence(const uint8_t frame[64])
{
    return (uint16_t)frame[4] | (uint16_t)frame[5] << 8;
}
