#include "ble_control.h"
#include "ble_packet.h"
#include "fpga_link.h"
#include "touch_output.h"
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gap_ble_api.h"
#include "esp_gatts_api.h"
#include "esp_gatt_common_api.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

enum {SERVICE, RX_DECL, RX_VALUE, TX_DECL, TX_VALUE, TX_CCC, ATTRIBUTE_COUNT};
static uint16_t handles[ATTRIBUTE_COUNT],connection;
static esp_gatt_if_t server=ESP_GATT_IF_NONE;
static _Atomic bool connected,subscribed,stop_requested;
static _Atomic bool congested;
static _Atomic unsigned negotiated_mtu=23;
static bool service_ready;
static _Atomic unsigned generation;
static touch_serial_command_handler_t handler;
static QueueHandle_t jobs,events;
static _Atomic bool event_loss;
void ble_control_event(const char *line){if(!events||!connected||!subscribed)return;char msg[48];size_t n=strlen(line);if(n>46)return;memcpy(msg,line,n+1);if(xQueueSend(events,msg,0)!=pdTRUE)event_loss=true;}
static TaskHandle_t worker_handle;
static bool capture_failed;static size_t captured;static char capture[2048];
void ble_control_log(const char *line){if(!worker_handle||xTaskGetCurrentTaskHandle()!=worker_handle)return;if(!strncmp(line,"ERROR,",6))capture_failed=true;size_t n=strlen(line);if(n>sizeof(capture)-1-captured){capture_failed=true;n=sizeof(capture)-1-captured;}memcpy(capture+captured,line,n);captured+=n;capture[captured]=0;}
typedef ble_packet_t job_t;
static job_t assembly;
/* UUIDs are little-endian on the BLE wire. */
static uint8_t service_uuid[16]={0xd0,0x94,0x90,0x71,0x27,0xd8,0xe0,0xb6,0x47,0x4b,0x59,0x8e,0x01,0x00,0x6a,0xf1};
static uint8_t rx_uuid[16]={0xd0,0x94,0x90,0x71,0x27,0xd8,0xe0,0xb6,0x47,0x4b,0x59,0x8e,0x02,0x00,0x6a,0xf1};
static uint8_t tx_uuid[16]={0xd0,0x94,0x90,0x71,0x27,0xd8,0xe0,0xb6,0x47,0x4b,0x59,0x8e,0x03,0x00,0x6a,0xf1};
static uint16_t primary=ESP_GATT_UUID_PRI_SERVICE,decl=ESP_GATT_UUID_CHAR_DECLARE,ccc=ESP_GATT_UUID_CHAR_CLIENT_CONFIG;
static uint8_t write_prop=ESP_GATT_CHAR_PROP_BIT_WRITE,notify_prop=ESP_GATT_CHAR_PROP_BIT_NOTIFY;
static uint8_t initial[1]={0},ccc_value[2]={0};
static const esp_gatts_attr_db_t table[ATTRIBUTE_COUNT]={
 [SERVICE]={{ESP_GATT_AUTO_RSP},{ESP_UUID_LEN_16,(uint8_t*)&primary,ESP_GATT_PERM_READ,16,16,service_uuid}},
 [RX_DECL]={{ESP_GATT_AUTO_RSP},{ESP_UUID_LEN_16,(uint8_t*)&decl,ESP_GATT_PERM_READ,1,1,&write_prop}},
 [RX_VALUE]={{ESP_GATT_RSP_BY_APP},{ESP_UUID_LEN_128,rx_uuid,ESP_GATT_PERM_WRITE_ENCRYPTED,512,0,initial}},
 [TX_DECL]={{ESP_GATT_AUTO_RSP},{ESP_UUID_LEN_16,(uint8_t*)&decl,ESP_GATT_PERM_READ,1,1,&notify_prop}},
 [TX_VALUE]={{ESP_GATT_AUTO_RSP},{ESP_UUID_LEN_128,tx_uuid,ESP_GATT_PERM_READ,244,0,initial}},
 [TX_CCC]={{ESP_GATT_AUTO_RSP},{ESP_UUID_LEN_16,(uint8_t*)&ccc,ESP_GATT_PERM_READ|ESP_GATT_PERM_WRITE,2,2,ccc_value}}
};
static esp_ble_adv_data_t adv={.set_scan_rsp=false,.include_name=false,.include_txpower=false,.flag=ESP_BLE_ADV_FLAG_GEN_DISC|ESP_BLE_ADV_FLAG_BREDR_NOT_SPT,.service_uuid_len=16,.p_service_uuid=service_uuid};
static esp_ble_adv_data_t scan_response={.set_scan_rsp=true,.include_name=true};
static esp_ble_adv_params_t adv_params={.adv_int_min=0x40,.adv_int_max=0x80,.adv_type=ADV_TYPE_IND,.own_addr_type=BLE_ADDR_TYPE_PUBLIC,.channel_map=ADV_CHNL_ALL,.adv_filter_policy=ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY};
static unsigned adv_ready;
static _Atomic unsigned ack_success,ack_rejected,last_ack_id;

bool ble_control_host_command(const char *line) {
 if(!strcmp(line,"BLE,STATUS")) {
  char status[240];
  snprintf(status,sizeof(status),"BLE,STATE,VERSION,R15-HALL-v3.4.26-BLE,CONNECTED,%u,SUBSCRIBED,%u,MTU,%u,ACK_OK,%u,ACK_REJECT,%u,LAST_ID,%u,FPGA_FLAGS,0x%02X,LAST_BULK,%s\r\n",
   (unsigned)connected,(unsigned)subscribed,(unsigned)negotiated_mtu,(unsigned)ack_success,(unsigned)ack_rejected,(unsigned)last_ack_id,fpga_link_reply_flags(),fpga_link_bulk_error());
  touch_serial_write(status);return true;
 }
 if(!strcmp(line,"BLE,CANCEL")) {stop_requested=true;touch_serial_write("OK,BLE,CANCEL\r\n");return true;}
 if(!strcmp(line,"BLE,PROBE")) {
  /* Status-query opcode: tests the exact BLE raw-to-SPI route without notes. */
  static const uint8_t query[6]={0xa5,0xb3,0,0,0,0x16};
  bool ok=fpga_link_bulk_send(query,sizeof(query));char status[144];
  snprintf(status,sizeof(status),"%s,BLE,PROBE,RESULT,%s,FPGA_FLAGS,0x%02X\r\n",ok?"OK":"ERROR",fpga_link_bulk_error(),fpga_link_reply_flags());
  touch_serial_write(status);return true;
 }
 return false;
}
/* Lifecycle/MTU/connection parameters follow ESP-IDF v6.1 official
 * gatt_server_service_table and gatt_security_server examples (CC0/Unlicense).
 * SPI work stays in the worker; GATT callbacks only validate and enqueue. */
static void advertise_if_ready(void) {
 if(service_ready && adv_ready==3 && !connected) {
  esp_err_t e=esp_ble_gap_start_advertising(&adv_params);
  if(e!=ESP_OK)ESP_LOGE("BLE_CONTROL","Advertising failed: %s",esp_err_to_name(e));
 }
}
static bool notify_text(const char *bytes,size_t length,unsigned epoch) {
 for(size_t offset=0;offset<length;) {
  TickType_t until=xTaskGetTickCount()+pdMS_TO_TICKS(1000);
  while(congested&&connected&&epoch==generation&&(int32_t)(until-xTaskGetTickCount())>0)vTaskDelay(pdMS_TO_TICKS(1));
  if(!connected||!subscribed||epoch!=generation||congested)return false;
  unsigned max=negotiated_mtu>3?negotiated_mtu-3:20;if(max>244)max=244;
  size_t n=length-offset;if(n>max)n=max;
  esp_err_t e=esp_ble_gatts_send_indicate(server,connection,handles[TX_VALUE],n,(uint8_t*)bytes+offset,false);
  if(e!=ESP_OK){ESP_LOGW("BLE_CONTROL","Notify failed: %s",esp_err_to_name(e));esp_ble_gatts_close(server,connection);return false;}
  offset+=n;if(offset<length)vTaskDelay(pdMS_TO_TICKS(1));
 }
 return true;
}
static void reply(uint8_t id,unsigned code) {
 if(!connected||!subscribed)return;
 last_ack_id=id;if(code)ack_rejected++;else ack_success++;
 if(code)TOUCH_LOGW("BLE_ACK","id=%u rejected; bulk=%s flags=0x%02X",id,fpga_link_bulk_error(),fpga_link_reply_flags());
 char text[24];int n=snprintf(text,sizeof(text),"ACK,%u,%u\n",id,code);
 notify_text(text,n,generation);
}
static void worker(void *arg) {
 (void)arg;job_t job;worker_handle=xTaskGetCurrentTaskHandle();
 for(;;) {
  if(atomic_exchange(&stop_requested,false)) {
   static const uint8_t panic[24]={0xa5,0x0e,0,0,0,0xab,0xa5,0x52,0,0,0,0xf7,0xa5,6,0,0,0,0xa3,0xa5,3,1,0,0,0xa7};
   fpga_link_cancel_strums();fpga_link_bulk_send(panic,sizeof(panic));
  }
  if(xQueueReceive(jobs,&job,pdMS_TO_TICKS(10))!=pdTRUE){
   char event[48];if(atomic_exchange(&event_loss,false))strcpy(event,"EVT,LOSS\n");else if(xQueueReceive(events,event,0)!=pdTRUE)continue;
   notify_text(event,strlen(event),generation);
   continue;
  }
  if(job.generation!=generation)continue;
  bool ok=false;
  if(job.text) {job.bytes[job.length]=0;captured=0;capture_failed=false;
   if(!strcmp((char*)job.bytes,"PING")){touch_serial_write("PONG,R15-HALL-v3.4.26-BLE\r\n");ok=true;}
   else ok=handler((const char*)job.bytes);
   if(!ok&&!captured)touch_serial_write("ERROR,COMMAND,UNSUPPORTED\r\n");
   ok=ok&&!capture_failed;
   if(captured&&!notify_text(capture,captured,job.generation))continue;
  }
  else {
   ok=fpga_link_bulk_send(job.bytes,job.length);
   if(!ok){char reason[160];int n=snprintf(reason,sizeof(reason),"ERROR,FPGA,BULK,%s,FLAGS,0x%02X,LENGTH,%u,OPCODE,0x%02X\n",fpga_link_bulk_error(),fpga_link_reply_flags(),job.length,job.bytes[1]);notify_text(reason,n,job.generation);}
  }
  if(job.text&&captured&&capture[captured-1]!='\n')notify_text("\n",1,job.generation);
  if(job.generation==generation)reply(job.id,ok?0:1);
  char event[48];
  if(atomic_exchange(&event_loss,false)){strcpy(event,"EVT,LOSS\n");notify_text(event,strlen(event),generation);}
  else if(xQueueReceive(events,event,0)==pdTRUE)notify_text(event,strlen(event),generation);
 }
}
static void gap_callback(esp_gap_ble_cb_event_t event,esp_ble_gap_cb_param_t *p) {
 if(event==ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT&&p->adv_data_cmpl.status==ESP_BT_STATUS_SUCCESS)adv_ready|=1;
 if(event==ESP_GAP_BLE_SCAN_RSP_DATA_SET_COMPLETE_EVT&&p->scan_rsp_data_cmpl.status==ESP_BT_STATUS_SUCCESS)adv_ready|=2;
 if(event==ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT||event==ESP_GAP_BLE_SCAN_RSP_DATA_SET_COMPLETE_EVT)advertise_if_ready();
 if(event==ESP_GAP_BLE_SEC_REQ_EVT)esp_ble_gap_security_rsp(p->ble_security.ble_req.bd_addr,true);
 if(event==ESP_GAP_BLE_AUTH_CMPL_EVT){ESP_LOGI("BLE_CONTROL","Pairing success=%u reason=0x%x",p->ble_security.auth_cmpl.success,p->ble_security.auth_cmpl.fail_reason);if(!p->ble_security.auth_cmpl.success&&connected)esp_ble_gatts_close(server,connection);}
 if(event==ESP_GAP_BLE_UPDATE_CONN_PARAMS_EVT)ESP_LOGI("BLE_CONTROL","Connection interval=%u latency=%u status=%u",p->update_conn_params.conn_int,p->update_conn_params.latency,p->update_conn_params.status);
}
static void gatt_callback(esp_gatts_cb_event_t event,esp_gatt_if_t interface,esp_ble_gatts_cb_param_t *p) {
 switch(event) {
 case ESP_GATTS_REG_EVT:
  if(p->reg.status!=ESP_GATT_OK){ESP_LOGE("BLE_CONTROL","GATT registration failed");break;}
  server=interface;esp_ble_gap_set_device_name("FPGA-V16-BLE");
  esp_ble_gap_config_adv_data(&adv);esp_ble_gap_config_adv_data(&scan_response);
  esp_ble_gatts_create_attr_tab(table,interface,ATTRIBUTE_COUNT,0);break;
 case ESP_GATTS_CREAT_ATTR_TAB_EVT:
  if(p->add_attr_tab.status==ESP_GATT_OK&&p->add_attr_tab.num_handle==ATTRIBUTE_COUNT){memcpy(handles,p->add_attr_tab.handles,sizeof(handles));esp_ble_gatts_start_service(handles[SERVICE]);}break;
 case ESP_GATTS_START_EVT:
  service_ready=p->start.status==ESP_GATT_OK;advertise_if_ready();break;
 case ESP_GATTS_CONNECT_EVT: {
  if(connected){esp_ble_gatts_close(interface,p->connect.conn_id);break;}
  connection=p->connect.conn_id;connected=true;subscribed=congested=false;negotiated_mtu=23;memset(&assembly,0,sizeof(assembly));generation++;
  esp_ble_conn_update_params_t params={0};memcpy(params.bda,p->connect.remote_bda,sizeof(params.bda));
  params.min_int=6;params.max_int=12;params.latency=0;params.timeout=400;esp_ble_gap_update_conn_params(&params);
  esp_ble_set_encryption(p->connect.remote_bda,ESP_BLE_SEC_ENCRYPT);break;
 }
 case ESP_GATTS_DISCONNECT_EVT:
  if(!connected||p->disconnect.conn_id!=connection)break;
  TOUCH_LOGI("BLE_CONTROL","DISCONNECT reason=0x%02X ack_ok=%u ack_rejected=%u",p->disconnect.reason,(unsigned)ack_success,(unsigned)ack_rejected);
  connected=subscribed=congested=false;memset(&assembly,0,sizeof(assembly));generation++;xQueueReset(jobs);xQueueReset(events);event_loss=false;stop_requested=true;advertise_if_ready();break;
 case ESP_GATTS_MTU_EVT:
  negotiated_mtu=p->mtu.mtu;ESP_LOGI("BLE_CONTROL","MTU=%u",p->mtu.mtu);break;
 case ESP_GATTS_CONGEST_EVT:
  congested=p->congest.congested;break;
 case ESP_GATTS_WRITE_EVT: {
  if(p->write.handle==handles[TX_CCC]){subscribed=p->write.len==2&&(p->write.value[0]&1);break;}
  if(p->write.handle!=handles[RX_VALUE])break;
  esp_gatt_status_t status=ESP_GATT_OK;
  uint8_t *b=p->write.value;unsigned n=p->write.len;
  if(!subscribed||p->write.is_prep||p->write.offset)status=ESP_GATT_REQ_NOT_SUPPORTED;
  else {
   int result=ble_packet_feed(&assembly,b,n,generation);
   if(result<0)status=ESP_GATT_INVALID_ATTR_LEN;
   else if(result>0&&xQueueSend(jobs,&assembly,0)!=pdTRUE)status=ESP_GATT_NO_RESOURCES;
  }
  if(p->write.need_rsp)esp_ble_gatts_send_response(interface,p->write.conn_id,p->write.trans_id,status,NULL);
  break;
 }
 default:break;
 }
}
esp_err_t ble_control_start(touch_serial_command_handler_t command_handler) {
 handler=command_handler;if(!handler)return ESP_ERR_INVALID_ARG;
 esp_err_t e=nvs_flash_init();if(e!=ESP_OK)return e; /* Preserve existing NVS on error. */
 esp_bt_controller_config_t config=BT_CONTROLLER_INIT_CONFIG_DEFAULT();
 e=esp_bt_controller_init(&config);if(e!=ESP_OK)return e;
 e=esp_bt_controller_enable(ESP_BT_MODE_BLE);if(e!=ESP_OK)return e;
 e=esp_bluedroid_init();if(e!=ESP_OK)return e;e=esp_bluedroid_enable();if(e!=ESP_OK)return e;
 events=xQueueCreate(32,48);jobs=xQueueCreate(4,sizeof(job_t));if(!events||!jobs)return ESP_ERR_NO_MEM;
 e=esp_ble_gap_register_callback(gap_callback);if(e!=ESP_OK)return e;
 e=esp_ble_gatts_register_callback(gatt_callback);if(e!=ESP_OK)return e;
 uint8_t auth=ESP_LE_AUTH_BOND,io=ESP_IO_CAP_NONE,key_size=16;
 esp_ble_gap_set_security_param(ESP_BLE_SM_AUTHEN_REQ_MODE,&auth,1);
 esp_ble_gap_set_security_param(ESP_BLE_SM_IOCAP_MODE,&io,1);
 esp_ble_gap_set_security_param(ESP_BLE_SM_MAX_KEY_SIZE,&key_size,1);
 uint8_t keys=ESP_BLE_ENC_KEY_MASK|ESP_BLE_ID_KEY_MASK;
 esp_ble_gap_set_security_param(ESP_BLE_SM_SET_INIT_KEY,&keys,1);
 esp_ble_gap_set_security_param(ESP_BLE_SM_SET_RSP_KEY,&keys,1);
 e=esp_ble_gatt_set_local_mtu(247);if(e!=ESP_OK)return e;
 e=esp_ble_gatts_app_register(0x16);if(e!=ESP_OK)return e;
 return xTaskCreate(worker,"ble_control",6144,NULL,3,NULL)==pdPASS?ESP_OK:ESP_ERR_NO_MEM;
}
