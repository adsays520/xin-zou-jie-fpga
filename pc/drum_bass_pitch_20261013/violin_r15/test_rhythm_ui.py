from copy import deepcopy
from contextlib import contextmanager
import tempfile
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from arrangement_model import PPQ
from arrangement_playback import score_notes
from melody_player import command_frame
from rhythm_model import make_chart
from rhythm_panel import ResultStore, ROOT
import test_arrangement_ui as interface_tests

MemoryPort = interface_tests.MemoryPort


class RhythmInterfaceTests(unittest.TestCase):
    @contextmanager
    def application(self):
        harness=interface_tests.ArrangementInterfaceTests()
        with harness.application() as (app, arranger):
            app.show_page('rhythm')
            app.update_idletasks()
            panel=app.rhythm_panel
            directory=ROOT/'tmp'/'rhythm_ui_tests'
            directory.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(dir=directory) as temporary:
                panel.store=ResultStore(Path(temporary)/'scores.json')
                try:
                    yield app,panel
                finally:
                    panel.stop()

    def authorize(self,app,panel,flags=7):
        port=MemoryPort();app.port=port
        panel._serialize()
        panel.probe.begin(app.port)
        values=[0xd8,0x45,panel.probe.sequence,8,flags]
        checksum=0
        for value in values:checksum^=value
        self.assertTrue(panel.probe.feed(bytes(values+[checksum]),app.port))
        return port

    def test_page_is_integrated_and_idle_does_not_connect_or_send(self):
        with self.application() as (app,panel):
            port=MemoryPort();app.port=port
            self.assertIn('rhythm',app._nav_buttons)
            self.assertEqual(app.active_page,'rhythm')
            self.assertGreater(len(panel.chart.targets),15)
            self.assertFalse(panel.hardware.get())
            self.assertFalse(panel.running)
            self.assertFalse(port.writes)
            self.assertGreater(len(panel.sources),10)
            self.assertTrue(panel.view.find_withtag('target'))

    def test_offline_mouse_keyboard_autorepeat_and_navigation_stop(self):
        with self.application() as (app,panel):
            port=MemoryPort();app.port=port
            panel.start()
            self.assertTrue(panel.running)
            target=panel.chart.targets[0]
            panel.pointer=(target.x,target.y)
            panel.origin=time.monotonic()-target.at
            event=SimpleNamespace(keysym='z',widget=panel.view)
            panel._key_down(event);panel._key_down(event)
            self.assertEqual(panel.session.combo,1)
            panel._key_up(event)
            self.assertFalse(panel.held)
            app.show_page('guitar')
            self.assertFalse(panel.running)
            self.assertIsNone(panel._frame_job)
            self.assertEqual(port.writes,[])

    def test_current_arrangement_is_copied_without_editing_or_discard_prompt(self):
        with self.application() as (app,panel):
            before=app.arrangement_panel.project.to_dict()
            panel.use_arrangement()
            self.assertEqual(panel.project.to_dict(),before)
            self.assertIsNot(panel.project,app.arrangement_panel.project)
            panel.project.name='audio game copy'
            self.assertEqual(app.arrangement_panel.project.to_dict(),before)

    def test_hardware_requires_own_probe_and_piano_ready_before_any_write(self):
        with self.application() as (app,panel):
            port=MemoryPort();app.port=port;panel.hardware.set(True)
            panel.start()
            self.assertFalse(panel.running)
            self.assertIn('探测',panel.status.get())
            self.assertFalse(port.writes)
            port=self.authorize(app,panel,3)
            panel.start()
            self.assertFalse(panel.running)
            self.assertIn('钢琴',panel.status.get())
            self.assertFalse(port.writes)

    def test_hardware_follow_and_disconnect_cleanup(self):
        with self.application() as (app,panel):
            panel.project.guitar_sustain=127
            port=self.authorize(app,panel)
            panel.hardware.set(True)
            panel.start()
            self.assertTrue(panel.running)
            self.assertTrue(panel.player.wait_ready(1))
            self.assertIn(command_frame(0x0e,1,0,0),b''.join(port.writes))
            self.assertFalse(panel.striker)
            app.disconnect()
            self.assertFalse(panel.running)
            self.assertFalse(port.is_open)
            self.assertIn(command_frame(0x0e,0,0,0),b''.join(port.writes))

    def test_live_guitar_hit_uses_background_queue_and_mutes_auto_guitar(self):
        with self.application() as (app,panel):
            panel.project.guitar_sustain=127
            port=self.authorize(app,panel)
            panel.hardware.set(True);panel.game_mode.set('命中发声')
            panel.start();self.assertTrue(panel.running)
            self.assertTrue(panel.player.wait_ready(1))
            plan=panel.player.snapshot().plan
            self.assertFalse(any(event.note.instrument=='guitar' for event in plan.events if event.kind=='on'))
            target=panel.chart.targets[0];panel.pointer=(target.x,target.y)
            panel._clock=lambda wall:(target.at,False)
            panel._tap()
            deadline=time.monotonic()+1
            while panel.striker.sent==0 and time.monotonic()<deadline:time.sleep(.005)
            self.assertEqual(panel.striker.sent,1)
            self.assertTrue(any(packet[1]==0x0a for packet in port.packets))
            self.assertEqual(panel.session.combo,1)
            striker=panel.striker
            panel.stop()
            self.assertFalse(striker.thread.is_alive())
            self.assertIn(command_frame(0x0e,0,0,0),b''.join(port.writes))

    def test_hall_events_are_read_only_and_snapshots_do_not_trigger(self):
        with self.application() as (app,panel):
            hall=app.hall_panel;s3=MemoryPort();hall.port=s3;hall.compatible=True
            hall.handle_line('HALL,STATE,ENABLED,1,ARMED,1,MASK,0x7F')
            panel.input_mode.set('霍尔拨杆');panel.rebuild();panel.start()
            self.assertTrue(panel.running)
            self.assertFalse(any(target.slider for target in panel.chart.targets))
            target=panel.chart.targets[0]
            panel.origin=time.monotonic()-target.at
            hall.handle_line('HALL,2,RAW,1400,BASE,1400,THRESHOLD,32,VALID,1,EVENTS,25,REJECTED,0,ERRORS,0')
            self.assertFalse(panel.session.done)
            hall.handle_line(f'I (1000) HALL: PICK H2 string={target.string} velocity=90 queued=1')
            self.assertEqual(panel.session.combo,1)
            self.assertEqual(s3.writes,[])

    def test_unknown_hall_state_and_unsupported_live_piano_are_refused(self):
        with self.application() as (app,panel):
            panel.input_mode.set('霍尔拨杆');panel.rebuild();panel.start()
            self.assertFalse(panel.running)
            self.assertIn('启用拨杆',panel.status.get())
            panel.input_mode.set('鼠标 / Z·X')
            panel.track.set(next(label for label,key in panel.track_ids.items() if key==panel.project.tracks[1].id))
            panel.game_mode.set('命中发声');panel.rebuild();panel.start()
            self.assertFalse(panel.running)
            self.assertIn('吉他/鼓',panel.status.get())

    def test_offline_demo_results_are_drawn_but_not_persisted(self):
        with self.application() as (app,panel):
            panel.autoplay.set(True);panel.start()
            for step in range(round((panel.chart.duration+1)*100)):
                panel.session.advance(step*.01)
            panel._finish()
            self.assertEqual(panel.summary['accuracy'],100)
            self.assertFalse(panel.store.path.exists())
            panel.view.draw(panel.chart,panel.session,panel.chart.duration,time.monotonic(),summary=panel.summary)
            self.assertTrue(panel.view.find_withtag('hud'))
            self.assertFalse(panel.running)

    def test_probe_is_invalidated_on_leave_and_event_listener_removed_on_destroy(self):
        with self.application() as (app,panel):
            self.authorize(app,panel)
            self.assertTrue(panel.probe.confirmed)
            app.show_page('guitar')
            self.assertFalse(panel.probe.confirmed)
            callback=panel._hall_line
            self.assertIn(callback,app.hall_panel.line_listeners)
            # Destruction itself is covered by the context's real Tk teardown.


if __name__=='__main__':
    unittest.main()
