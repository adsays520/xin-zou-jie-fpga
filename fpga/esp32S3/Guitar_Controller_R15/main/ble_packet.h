#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
typedef struct {
    uint8_t id;
    bool text, collecting;
    uint16_t length;
    unsigned generation;
    uint8_t bytes[267];
} ble_packet_t;
/* -1 invalid, 0 incomplete, 1 complete. FIRST replaces an old partial packet. */
static inline int ble_packet_feed(ble_packet_t *p,const uint8_t *data,size_t size,unsigned epoch)
{
    if(size<3||size>246||(data[0]&~7U))goto invalid;
    bool first=(data[0]&1)!=0,last=(data[0]&2)!=0,text=(data[0]&4)!=0;
    if(first)*p=(ble_packet_t){.id=data[1],.text=text,.collecting=true,.generation=epoch};
    if(!p->collecting||p->generation!=epoch||p->id!=data[1]||p->text!=text||p->length+size-2>266)goto invalid;
    if(text)for(size_t i=2;i<size;++i)if(!data[i]||data[i]=='\r'||data[i]=='\n')goto invalid;
    memcpy(p->bytes+p->length,data+2,size-2);p->length+=size-2;
    if(last){p->collecting=false;if(!text&&p->length<6)goto invalid;p->bytes[p->length]=0;return 1;}
    return 0;
invalid:
    p->collecting=false;p->length=0;return -1;
}
