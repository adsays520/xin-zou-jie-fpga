"""Execute the real Java queue/ACK methods with a minimal platform harness."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import os, shutil
JAVA = Path(os.environ['JAVA_HOME']) / 'bin' if os.environ.get('JAVA_HOME') else Path(shutil.which('javac') or 'javac').resolve().parent


def method(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class AndroidAckTests(unittest.TestCase):
    def test_rejected_packet_cancels_jobs_keeps_link_and_allows_next_packet(self):
        source = (ROOT / 'android/app/src/main/java/cn/fpga/controller/MainActivity.java').read_text()
        methods = '\n'.join(method(source, name) for name in
                            ('void pump()', 'void completePacket()', 'void rejectPacket()'))
        harness = r'''
import java.util.*;
import java.nio.charset.StandardCharsets;
public class AckRegression {
 static class Handler {void removeCallbacks(Runnable r){} void postDelayed(Runnable r,long d){}}
 static class SystemClock {static long uptimeMillis(){return 1000;}}
 static class Job {byte[] bytes;boolean text,cleanup=false;int delay=0;Job(byte[] b,boolean t){bytes=b;text=t;}}
 Handler handler=new Handler(); Runnable deadline=()->{},resumePump=()->{};
 ArrayDeque<Job> queue=new ArrayDeque<>();
 boolean ready=true,currentCleanup=false,currentText=false,writing=false,ackReceived=false;
 byte[] current;long cooldownUntil=0;int currentDelay=0,id=3,offset=0,ackCode=1;
 String idleTicket="old upload";int closeCalls=0,writes=0;List<String> messages=new ArrayList<>();
 void writeChunk(){writes++;writing=true;offset=current.length;}
 void closeLink(String reason){closeCalls++;ready=false;}
 void reportQueue(){}
 void js(String event,String value){messages.add(event+":"+value);}
 static void require(boolean b,String why){if(!b)throw new AssertionError(why);}
 METHODS
 public static void main(String[] args){
  AckRegression a=new AckRegression();a.current=new byte[]{1,2,3};
  a.queue.add(new Job(new byte[]{99},false));
  a.completePacket();
  require(a.ready&&a.closeCalls==0,"negative ACK closed BLE");
  require(a.queue.isEmpty()&&a.currentCleanup,"old jobs must be discarded");
  require(new String(a.current,StandardCharsets.UTF_8).equals("BLE,CANCEL"),"one cleanup expected");
  require(a.id==4&&a.writes==1&&a.idleTicket==null,"cleanup state");
  require(a.messages.get(0).contains("ACK,3,1"),"rejected ID must remain original");
  a.ackCode=1;a.completePacket();
  require(a.ready&&a.current==null&&a.writes==1,"rejected cleanup must not loop");
  a.queue.add(new Job(new byte[]{42},false));a.pump();
  require(!a.currentCleanup&&a.id==5,"next user command must work");
  a.ackCode=0;a.completePacket();
  require(a.ready&&a.current==null&&a.closeCalls==0,"positive ACK must complete");
  System.out.println("PASS: ACK rejection keeps BLE; queue canceled; one cleanup; subsequent command accepted");
 }
}
'''.replace('METHODS', methods)
        with tempfile.TemporaryDirectory(prefix='ble_ack_') as temp:
            path = Path(temp) / 'AckRegression.java'
            path.write_text(harness, encoding='utf-8')
            compiled = subprocess.run([str(JAVA/'javac.exe'), '-encoding', 'UTF-8', str(path)],
                                      capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout+compiled.stderr)
            result = subprocess.run([str(JAVA/'java.exe'), '-cp', temp, 'AckRegression'],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
