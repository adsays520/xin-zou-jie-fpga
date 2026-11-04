package cn.fpga.controller;



import android.Manifest;

import android.app.*;

import android.os.*;

import android.bluetooth.*;

import android.bluetooth.le.*;

import android.content.*;

import android.content.pm.PackageManager;

import android.webkit.*;

import android.net.Uri;

import java.util.*;

import java.nio.charset.StandardCharsets;

import org.json.JSONObject;



/** Local UI + BLE only. Sound is synthesized on FPGA, never on the phone. */

public class MainActivity extends Activity {

 static final UUID SERVICE=UUID.fromString("f16a0001-8e59-4b47-b6e0-d827719094d0");

 static final UUID RX=UUID.fromString("f16a0002-8e59-4b47-b6e0-d827719094d0"),TX=UUID.fromString("f16a0003-8e59-4b47-b6e0-d827719094d0");

 static final UUID CCC=UUID.fromString("00002902-0000-1000-8000-00805f9b34fb");

 final Handler handler=new Handler(Looper.getMainLooper());

 WebView web; BluetoothAdapter adapter; BluetoothGatt gatt; BluetoothGattCharacteristic rx,tx;

 boolean ready=false,scanning=false; int mtu=23,id=0,offset=0; byte[] current; boolean currentText; boolean writing=false,ackReceived=false; int ackCode=0; final StringBuilder incoming=new StringBuilder();

 long cooldownUntil=0;int currentDelay=0;boolean currentCleanup=false;String idleTicket=null;final Runnable resumePump=()->pump();

 final ArrayDeque<Job> queue=new ArrayDeque<>();

 final LinkedHashMap<String,BluetoothDevice> devices=new LinkedHashMap<>();

 PermissionRequest audioRequest;

 ValueCallback<Uri[]> chooser; String saveData;

 static class Job { byte[] bytes;boolean text,cleanup=false;int delay=0;Job(byte[] b,boolean t){bytes=b;text=t;} }

 void js(String event,String value){handler.post(()->web.evaluateJavascript("window.nativeEvent&&nativeEvent("+JSONObject.quote(event)+","+JSONObject.quote(value)+")",null));}

 @Override public void onCreate(Bundle b){super.onCreate(b);web=new WebView(this);setContentView(web);

  web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);

  web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(true);

  web.addJavascriptInterface(new Bridge(),"Mobile");

  web.setWebViewClient(new WebViewClient(){

   @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !"fpga.local".equals(r.getUrl().getHost());}

   @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){

    String path=r.getUrl().getPath();if(!"fpga.local".equals(r.getUrl().getHost())||path==null||path.contains(".."))return new WebResourceResponse("text/plain","UTF-8",new java.io.ByteArrayInputStream(new byte[0]));

    try{String mime=path.endsWith(".js")?"application/javascript":path.endsWith(".json")?"application/json":"text/html";return new WebResourceResponse(mime,"UTF-8",getAssets().open(path.substring(1)));}catch(Exception e){return new WebResourceResponse("text/plain","UTF-8",new java.io.ByteArrayInputStream(new byte[0]));}

   }

  });

  web.setWebChromeClient(new WebChromeClient(){

   @Override public void onPermissionRequest(PermissionRequest request){runOnUiThread(()->{if(!"fpga.local".equals(request.getOrigin().getHost())||!Arrays.asList(request.getResources()).contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE)){request.deny();return;}audioRequest=request;if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED){request.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});audioRequest=null;}else requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},8);});}

@Override public boolean onShowFileChooser(WebView v,ValueCallback<Uri[]> cb,FileChooserParams p){if(chooser!=null)chooser.onReceiveValue(null);chooser=cb;Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,31);return true;}});

  web.loadUrl("https://fpga.local/index.html");adapter=((BluetoothManager)getSystemService(BLUETOOTH_SERVICE)).getAdapter();

 }

 class Bridge {

  @JavascriptInterface public void openMidiResource(String key){handler.post(()->{
   String url="mutopia".equals(key)?"https://www.mutopiaproject.org/":"commons".equals(key)?"https://commons.wikimedia.org/wiki/Category:MIDI_files":"bitmidi".equals(key)?"https://bitmidi.com/":null;
   if(url==null){js("error","未知MIDI资源入口");return;}
   try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)).addCategory(Intent.CATEGORY_BROWSABLE));}catch(ActivityNotFoundException e){js("error","请安装浏览器后打开资源网站");}
  });}
  @JavascriptInterface public String midiSample(String key){
   String name="twinkle".equals(key)?"Twinkle_Star.mid":"harbor".equals(key)?"04_Star_Harbor.mid":"retrigger".equals(key)?"02_Echo_Retrigger.mid":null;
   if(name==null)return "";
   try(java.io.InputStream in=getAssets().open("midi/"+name);java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){
    byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>4000000)return "";out.write(b,0,n);}return android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP);
   }catch(Exception e){return "";}
  }


  @JavascriptInterface public void scan(){handler.post(()->beginScan());}

  @JavascriptInterface public void disconnect(){handler.post(()->closeLink("已断开"));}

  @JavascriptInterface public void clearQueue(){handler.post(()->{queue.clear();idleTicket=null;currentDelay=0;cooldownUntil=0;handler.removeCallbacks(resumePump);js("queue",current==null?"0":"1");});}

  @JavascriptInterface public void whenIdle(String ticket){handler.post(()->{idleTicket=ticket;reportQueue();});}

  @JavascriptInterface public void send(String hex,boolean text){handler.post(()->{

   if(!ready){js("error","请先连接配套BLE固件");return;}

   if(!hex.matches("[0-9a-fA-F]+")||hex.length()%2!=0||hex.length()>532||queue.size()>2000){closeLink("发送失败：数据格式错误或队列过长");return;}

   byte[] data=new byte[hex.length()/2];for(int i=0;i<data.length;i++)data[i]=(byte)Integer.parseInt(hex.substring(i*2,i*2+2),16);

   queue.add(new Job(data,text));pump();reportQueue();

  });}

  @JavascriptInterface public void sendWithDelay(String hex,boolean text,int delay){handler.post(()->{

   if(!ready||!hex.matches("[0-9a-fA-F]+")||hex.length()%2!=0||hex.length()>532||queue.size()>2000){closeLink("准备失败：未连接、数据不正确或队列过长");return;}

   byte[] data=new byte[hex.length()/2];for(int i=0;i<data.length;i++)data[i]=(byte)Integer.parseInt(hex.substring(i*2,i*2+2),16);

   Job j=new Job(data,text);j.delay=Math.max(0,Math.min(1000,delay));queue.add(j);pump();reportQueue();

  });}

  @JavascriptInterface public String demo(String name){if(!name.matches("[a-zA-Z0-9_]+\\.tang\\.json"))return "";try(java.io.InputStream in=getAssets().open("demos/"+name);java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}catch(Exception e){return "";}}

  @JavascriptInterface public void saveTang(String data){handler.post(()->{if(data.length()>4000000)return;saveData=data;startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,"手机编曲.tang.json"),32);});}

  @JavascriptInterface public void save(String data){handler.post(()->{if(data.length()>4000000){js("error","工程超过4MB");return;}saveData=data;startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,"FPGA_mobile.json"),32);});}

 }

 boolean permissions(){if(Build.VERSION.SDK_INT>=31)return checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED&&checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED;return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED;}

 void beginScan(){if(adapter==null){js("error","手机不支持蓝牙");return;}if(!permissions()){requestPermissions(Build.VERSION.SDK_INT>=31?new String[]{Manifest.permission.BLUETOOTH_SCAN,Manifest.permission.BLUETOOTH_CONNECT}:new String[]{Manifest.permission.ACCESS_FINE_LOCATION},7);return;}if(!adapter.isEnabled()){startActivity(new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE));return;}

  stopScan();devices.clear();scanning=true;js("state","扫描配套FPGA BLE设备…");

  adapter.getBluetoothLeScanner().startScan(Collections.singletonList(new ScanFilter.Builder().setServiceUuid(new ParcelUuid(SERVICE)).build()),new ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(),scanCallback);

  handler.postDelayed(()->{stopScan();if(devices.isEmpty()){js("error","未发现设备；原V16未启用BLE，须烧入本次配套S3固件");return;}ArrayList<BluetoothDevice> list=new ArrayList<>(devices.values());String[] names=new String[list.size()];for(int i=0;i<names.length;i++)names[i]=String.valueOf(list.get(i).getName())+"\n"+list.get(i).getAddress();new AlertDialog.Builder(this).setTitle("选择设备").setItems(names,(d,n)->connect(list.get(n))).setNegativeButton("取消",null).show();},6500);

 }

 final ScanCallback scanCallback=new ScanCallback(){@Override public void onScanResult(int type,ScanResult r){handler.post(()->devices.put(r.getDevice().getAddress(),r.getDevice()));}@Override public void onScanFailed(int e){js("error","扫描失败："+e);}};

 void stopScan(){if(scanning&&adapter!=null&&adapter.isEnabled())adapter.getBluetoothLeScanner().stopScan(scanCallback);scanning=false;}

 void connect(BluetoothDevice d){closeLink("连接中…");gatt=d.connectGatt(this,false,callback,BluetoothDevice.TRANSPORT_LE);}

 void closeLink(String reason){stopScan();ready=false;queue.clear();current=null;writing=false;ackReceived=false;incoming.setLength(0);idleTicket=null;handler.removeCallbacks(deadline);handler.removeCallbacks(resumePump);cooldownUntil=0;rx=null;tx=null;if(gatt!=null){gatt.disconnect();gatt.close();gatt=null;}js("state",reason);js("queue","0");}

 void reportQueue(){int depth=queue.size()+(current==null?0:1);js("queue",String.valueOf(depth));if(depth==0&&idleTicket!=null&&ready){long remaining=Math.max(0,cooldownUntil-SystemClock.uptimeMillis());if(remaining>0){handler.postDelayed(()->reportQueue(),remaining);return;}String ticket=idleTicket;idleTicket=null;js("idle",ticket);}}

 final Runnable deadline=()->closeLink("传输超时，队列已取消；重新连接后须从BEGIN重新上传，不能续传半包");

 void pump(){if(current!=null||queue.isEmpty()||!ready)return;if(SystemClock.uptimeMillis()<cooldownUntil){handler.removeCallbacks(resumePump);handler.postDelayed(resumePump,cooldownUntil-SystemClock.uptimeMillis());return;}Job j=queue.remove();currentDelay=j.delay;currentCleanup=j.cleanup;current=j.bytes;currentText=j.text;offset=0;ackReceived=false;writing=false;id=(id+1)&255;handler.removeCallbacks(deadline);handler.postDelayed(deadline,6000);writeChunk();}

 void writeChunk(){int count=Math.min(Math.max(1,Math.min(mtu-5,240)),current.length-offset);byte[] part=new byte[count+2];part[0]=(byte)((offset==0?1:0)|(offset+count==current.length?2:0)|(currentText?4:0));part[1]=(byte)id;System.arraycopy(current,offset,part,2,count);offset+=count;writing=true;rx.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT);rx.setValue(part);if(!gatt.writeCharacteristic(rx))closeLink("BLE写入启动失败");}

 void completePacket(){handler.removeCallbacks(deadline);if(ackCode!=0){rejectPacket();return;}current=null;cooldownUntil=SystemClock.uptimeMillis()+currentDelay;pump();reportQueue();}

 // A negative application ACK is a completed transaction, not a BLE link error.
 // Cancel future music/upload jobs and try one stop request, without reconnecting
 // or replaying the rejected packet. An old firmware rejecting CANCEL cannot loop.
 void rejectPacket(){boolean stop=!currentCleanup;int rejected=id;queue.clear();current=null;writing=false;ackReceived=false;idleTicket=null;currentDelay=0;cooldownUntil=0;handler.removeCallbacks(resumePump);if(stop&&ready){Job cleanup=new Job("BLE,CANCEL".getBytes(StandardCharsets.UTF_8),true);cleanup.cleanup=true;queue.add(cleanup);pump();}reportQueue();js("error","ACK,"+rejected+","+ackCode+"：板端拒收；已取消发送，蓝牙连接保留。上传请从BEGIN重传；具体原因见前一条ERROR回执。");}

 final BluetoothGattCallback callback=new BluetoothGattCallback(){

  @Override public void onConnectionStateChange(BluetoothGatt g,int status,int state){handler.post(()->{if(g!=gatt)return;if(status!=BluetoothGatt.GATT_SUCCESS||state==BluetoothProfile.STATE_DISCONNECTED){closeLink("蓝牙断开；未完成上传已取消");return;}if(state==BluetoothProfile.STATE_CONNECTED)g.discoverServices();});}

  @Override public void onServicesDiscovered(BluetoothGatt g,int status){handler.post(()->{if(g!=gatt)return;BluetoothGattService s=g.getService(SERVICE);if(status!=0||s==null){closeLink("服务不匹配");return;}rx=s.getCharacteristic(RX);tx=s.getCharacteristic(TX);if(rx==null||tx==null||!g.requestMtu(247)){closeLink("设备缺少控制通道");}});}

  @Override public void onMtuChanged(BluetoothGatt g,int m,int status){handler.post(()->{if(g!=gatt)return;if(status==0)mtu=m;g.setCharacteristicNotification(tx,true);BluetoothGattDescriptor c=tx.getDescriptor(CCC);if(c==null){closeLink("设备缺少通知通道");return;}c.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);if(!g.writeDescriptor(c))closeLink("通知订阅失败");});}

  @Override public void onDescriptorWrite(BluetoothGatt g,BluetoothGattDescriptor d,int status){handler.post(()->{if(g!=gatt)return;if(status!=0){closeLink("通知订阅失败："+status);return;}ready=true;js("state","BLE已连接；FPGA能力由每次指令的板端结果核验");});}

  @Override public void onCharacteristicWrite(BluetoothGatt g,BluetoothGattCharacteristic c,int status){handler.post(()->{if(g!=gatt||current==null)return;if(status!=0){closeLink("BLE拒收："+status);return;}writing=false;if(offset<current.length)writeChunk();else if(ackReceived)completePacket();});}

  @Override public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c){final String value=new String(c.getValue(),StandardCharsets.UTF_8);handler.post(()->{if(g!=gatt)return;incoming.append(value);if(incoming.length()>4096){incoming.setLength(0);return;}int newline;while((newline=incoming.indexOf("\n"))>=0){String line=incoming.substring(0,newline).trim();incoming.delete(0,newline+1);js("rx",line);String[] p=line.split(",");try{if(p.length>=3&&p[0].equals("ACK")&&current!=null&&Integer.parseInt(p[1])==id){ackReceived=true;ackCode=Integer.parseInt(p[2]);if(!writing&&offset==current.length)completePacket();}}catch(NumberFormatException ignored){js("error","无效设备回执");}}});}



 };

 @Override public void onRequestPermissionsResult(int r,String[] p,int[] v){super.onRequestPermissionsResult(r,p,v);if(r==8){if(audioRequest!=null){if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)audioRequest.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});else audioRequest.deny();audioRequest=null;}return;}if(r==7&&permissions())beginScan();else js("error","需要附近设备/旧Android定位权限才能扫描BLE");}

 @Override protected void onActivityResult(int r,int result,Intent data){super.onActivityResult(r,result,data);if(r==31&&chooser!=null){chooser.onReceiveValue(result==RESULT_OK&&data!=null?new Uri[]{data.getData()}:null);chooser=null;}if(r==32&&result==RESULT_OK&&data!=null&&saveData!=null){try(java.io.OutputStream out=getContentResolver().openOutputStream(data.getData())){out.write(saveData.getBytes(StandardCharsets.UTF_8));js("rx","工程已保存");}catch(Exception e){js("error",e.toString());}saveData=null;}}

 @Override protected void onPause(){super.onPause();if(web!=null)js("background","");}

 @Override protected void onDestroy(){closeLink("应用关闭");web.removeJavascriptInterface("Mobile");web.destroy();super.onDestroy();}

}

