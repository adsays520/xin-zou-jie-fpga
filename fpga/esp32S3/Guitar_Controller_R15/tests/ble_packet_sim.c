#include "../main/ble_packet.h"
#define API __declspec(dllexport)
static ble_packet_t packet;
API void packet_reset(void){memset(&packet,0,sizeof(packet));}
API int packet_feed(const uint8_t *bytes,unsigned length,unsigned epoch){return ble_packet_feed(&packet,bytes,length,epoch);}
API unsigned packet_length(void){return packet.length;}
API unsigned packet_byte(unsigned index){return packet.bytes[index];}
API unsigned packet_collecting(void){return packet.collecting;}
