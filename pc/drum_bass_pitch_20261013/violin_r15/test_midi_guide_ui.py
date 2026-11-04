from unittest.mock import patch
import unittest
from test_arrangement_ui import ArrangementInterfaceTests, MemoryPort
from midi_guide import MidiScore, MidiNote

class MidiGuideInterfaceTests(unittest.TestCase):
    application = ArrangementInterfaceTests.application

    def prepare(self, app):
        panel=app.midi_guide_panel
        panel.score=MidiScore((MidiNote(0,1,40,100,0,0),),('Melody',),2)
        panel.notes=panel.score.notes
        port=MemoryPort(); app.hall_panel.port=port; app.hall_panel.compatible=True
        app.show_page('midi_guide')
        return panel,port

    def test_capability_pause_and_clear(self):
        with self.application() as (app,_):
            panel,port=self.prepare(app); panel.play()
            self.assertEqual(port.writes,[b'LED,GUIDE,STATUS\n'])
            self.assertFalse(panel.running)
            panel.line('LED,GUIDE,CAP,1,TTL_MS,1000',0); panel.tick()
            self.assertTrue(panel.running)
            self.assertIn(b'LED,GUIDE,1,20\n',port.writes)
            panel.pause(); self.assertEqual(port.writes[-1],b'LED,GUIDE,0,0\n')

    def test_seek_hide_reconnect(self):
        with self.application() as (app,_):
            panel,port=self.prepare(app); panel.capable_port=port
            panel.play(); panel.seek('.5')
            self.assertFalse(panel.running); self.assertEqual(panel.position,.5)
            panel.play(); app.show_page('guitar')
            self.assertFalse(panel.running); self.assertEqual(port.writes[-1],b'LED,GUIDE,0,0\n')
            app.show_page('midi_guide'); panel.play()
            replacement=MemoryPort(); app.hall_panel.port=replacement; panel.tick()
            self.assertFalse(panel.running); self.assertEqual(replacement.writes,[])
            panel.play(); self.assertEqual(replacement.writes,[b'LED,GUIDE,STATUS\n'])

    def test_speed_resume_completion(self):
        with self.application() as (app,_):
            panel,port=self.prepare(app); panel.capable_port=port; panel.speed.set(50)
            with patch('midi_guide_panel.time.monotonic',return_value=100): panel.play()
            with patch('midi_guide_panel.time.monotonic',return_value=102): panel.pause()
            self.assertEqual(panel.position,1)
            with patch('midi_guide_panel.time.monotonic',return_value=200): panel.play()
            self.assertEqual(panel.origin,198)
            with patch('midi_guide_panel.time.monotonic',return_value=202): panel.tick()
            self.assertFalse(panel.running); self.assertEqual(port.writes[-1],b'LED,GUIDE,0,0\n')

    def test_invalid_and_unknown_firmware(self):
        with self.application() as (app,_):
            panel,port=self.prepare(app); panel.speed.set(0); panel.play()
            self.assertFalse(panel.running); self.assertEqual(port.writes,[])
            panel.speed.set(100); panel.play()
            with patch('midi_guide_panel.time.monotonic',return_value=panel.await_until+1): panel.tick()
            self.assertFalse(panel.running); self.assertIn('配套',panel.status.get())

if __name__=='__main__':unittest.main()
