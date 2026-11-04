"""Execute the actual native browser bridge against an intent-capture harness."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_android_ack import method, JAVA, ROOT


class ResourceBridgeTests(unittest.TestCase):
    def test_only_known_https_resources_launch_external_browser(self):
        source=(ROOT/'android/app/src/main/java/cn/fpga/controller/MainActivity.java').read_text(encoding='utf8')
        action=method(source,'public void openMidiResource(String key)')
        harness='''import java.util.*;
public class ResourceBridge {
 static class Handler {void post(Runnable r){r.run();}}
 static class Uri {static String parse(String s){return s;}}
 static class Intent {static String ACTION_VIEW="view",CATEGORY_BROWSABLE="browser";String url;Intent(String a,String u){url=u;}Intent addCategory(String c){return this;}}
 static class ActivityNotFoundException extends RuntimeException {}
 Handler handler=new Handler();List<String> urls=new ArrayList<>();List<String> errors=new ArrayList<>();boolean noBrowser;
 void startActivity(Intent intent){if(noBrowser)throw new ActivityNotFoundException();urls.add(intent.url);}
 void js(String kind,String text){errors.add(kind+":"+text);}
'''+action+'''
 public static void main(String[] a){ResourceBridge b=new ResourceBridge();
 b.openMidiResource("mutopia");b.openMidiResource("commons");b.openMidiResource("bitmidi");
 if(b.urls.size()!=3||!b.urls.get(0).equals("https://www.mutopiaproject.org/"))throw new AssertionError();
 for(String s:new String[]{null,"https://evil.invalid","javascript:alert(1)","file:///private","../mutopia"})b.openMidiResource(s);
 if(b.urls.size()!=3||b.errors.size()!=5)throw new AssertionError("unknown resource launched");
 b.noBrowser=true;b.openMidiResource("mutopia");if(b.errors.size()!=6)throw new AssertionError();
 System.out.println("PASS: native resource allowlist; unknown keys rejected; missing browser reported");}}
'''
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ResourceBridge.java';path.write_text(harness,encoding='utf8')
            subprocess.run([JAVA/'javac.exe','-encoding','UTF-8',str(path)],check=True,capture_output=True)
            result=subprocess.run([JAVA/'java.exe','-cp',folder,'ResourceBridge'],check=True,capture_output=True,text=True)
            self.assertIn('PASS:',result.stdout)
            print(result.stdout.strip())


if __name__=='__main__':unittest.main()
