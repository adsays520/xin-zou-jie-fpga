from contextlib import contextmanager
from pathlib import Path
import threading
import time
import unittest

from arrangement_model import BAR, Clip, Note, Project, Track
from arrangement_panel import ArrangementPanel
from arrangement_playback import ArrangementPlayer, compile_plan
from arrangement_worker import ThreadedArrangementPlayer
from serial_transport import PlaybackSender, SerializedPort
from test_arrangement import Clock
import test_arrangement_ui as interface_tests

MemoryPort = interface_tests.MemoryPort


def wait_until(predicate, timeout=1.5):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError('background condition timed out')
        time.sleep(0.005)


def short_plan(hardware=True):
    project = Project(bpm=300, bars=1, loop_end=BAR, tracks=[Track('piano', clips=[Clip(length=BAR, notes=[
        Note(start=0, duration=96, pitch=60), Note(start=192, duration=96, pitch=64),
        Note(start=384, duration=96, pitch=67)])])])
    return compile_plan(project, hardware, ensemble=True)


@contextmanager
def worker(send=None, **keywords):
    player = ThreadedArrangementPlayer(send, **keywords)
    try:
        yield player
    finally:
        if not player.shutdown(1):
            raise AssertionError('playback thread leaked')


class WorkerTests(unittest.TestCase):
    def test_worker_keeps_sending_while_main_thread_sleeps(self):
        sent = []
        owner = threading.get_ident()
        with worker(lambda data: sent.append((threading.get_ident(), bytes(data))) or True) as player:
            player.play(short_plan())
            self.assertTrue(player.wait_ready())
            time.sleep(0.45)  # Longer than the old Tk 150ms cutoff; no GUI polling.
            self.assertEqual(player.state, 'playing', player.message)
            frames = b''.join(data for _, data in sent)
            self.assertGreaterEqual(sum(frames[i + 1] == 0x0c for i in range(0, len(frames), 6)), 4)
            self.assertTrue(all(thread != owner for thread, _ in sent))
            self.assertLess(player.max_lateness, 0.15)

    def test_batched_wire_matches_original_for_five_instruments(self):
        project = Project(bpm=300, bars=1, loop_end=BAR, tracks=[Track(instrument, clips=[Clip(length=BAR, notes=[Note(pitch=pitch)])])
            for instrument, pitch in [('piano', 60), ('guitar', 64), ('bass', 28), ('violin', 67), ('drums', 0)]])
        plan = compile_plan(project, True, ensemble=True)
        clock, original = Clock(), []
        core = ArrangementPlayer(lambda data: original.append(data) or True, clock.schedule, clock.cancel,
                                 clock=lambda: clock.now)
        core.play(plan)
        clock.advance(plan.duration + 0.01)
        sent = []
        with worker(lambda data: sent.append(data) or True) as player:
            player.play(plan)
            wait_until(lambda: player.state == 'stopped')
            self.assertIn('播放完成', player.message)
        self.assertEqual(b''.join(sent), b''.join(original))
        self.assertLess(len(sent), len(original))
        self.assertEqual(sent[0], b''.join(event.data for event in plan.events if event.at == 0))

    def test_stalled_worker_clock_still_aborts_without_stale_attacks(self):
        shifted = [0]
        sent = []
        with worker(lambda data: sent.append(data) or True, clock=lambda: time.monotonic() + shifted[0]) as player:
            player.play(short_plan())
            self.assertTrue(player.wait_ready())
            shifted[0] = 0.5
            wait_until(lambda: player.state == 'stopped')
            self.assertIn('迟到超过150ms', player.message)
            frames = b''.join(sent)
            attacks = [frames[i + 2] for i in range(0, len(frames), 6) if frames[i + 1] == 0x0c and frames[i + 4]]
            self.assertEqual(attacks, [60])

    def test_stop_during_write_releases_accepted_notes_and_cancels_future(self):
        entered, release, sent = threading.Event(), threading.Event(), []
        def send(data):
            sent.append(data)
            if len(sent) == 1:
                entered.set()
                release.wait(1)
            return True
        with worker(send) as player:
            player.play(short_plan())
            self.assertTrue(entered.wait(1))
            started = time.monotonic()
            player.stop('测试停止')
            self.assertLess(time.monotonic() - started, 0.05)
            release.set()
            self.assertTrue(player.wait_ready())
            count = len(sent)
            time.sleep(0.25)
            self.assertEqual(len(sent), count)
            frames = b''.join(sent)
            self.assertIn(b'\xa5\x0c\x3c\x01\x00', frames)
            self.assertEqual(player.state, 'stopped')
            self.assertFalse(player.active)

    def test_transport_fault_requires_new_connection_and_keeps_reason(self):
        port = MemoryPort()
        port.write = lambda data: len(data) - 1
        old = SerializedPort(port)
        with worker() as player:
            player.play(short_plan(), send=PlaybackSender(old))
            self.assertTrue(player.wait_ready())
            self.assertIn('部分写入', player.message)
            self.assertIn('状态未知', player.message)
            player.play(short_plan(), send=PlaybackSender(old))
            self.assertTrue(player.wait_ready())
            self.assertIn('断开重连', player.message)
            new = MemoryPort()
            player.play(short_plan(), send=PlaybackSender(SerializedPort(new)))
            self.assertTrue(player.wait_ready())
            self.assertEqual(player.state, 'playing')
            self.assertTrue(new.writes)

    def test_offline_never_sends_and_loop_stops_cleanly(self):
        with worker(lambda data: self.fail('offline wrote serial')) as player:
            player.play(short_plan(False), loop=True)
            self.assertTrue(player.wait_ready())
            time.sleep(0.88)
            self.assertEqual(player.state, 'playing')
            player.stop()
            self.assertTrue(player.wait_ready())
            self.assertFalse(player.active)

    def test_connection_is_captured_and_rapid_restarts_are_ordered(self):
        old, new = MemoryPort(), MemoryPort()
        with worker() as player:
            player.play(short_plan(), send=PlaybackSender(SerializedPort(old)))
            self.assertTrue(player.wait_ready())
            with player._condition:  # Queue a deterministic superseded sequence.
                player.stop()
                player.play(short_plan(), send=PlaybackSender(SerializedPort(new)))
                player.stop()
                player.play(short_plan(False))
            self.assertTrue(player.wait_ready())
            self.assertEqual(player.state, 'playing')
            self.assertFalse(player.plan.hardware)
            self.assertFalse(new.writes)  # Superseded play never attacks the new port.
            old_count = len(old.writes)
            time.sleep(0.25)
            self.assertEqual(old_count, len(old.writes))

    def test_chord_retrigger_orders_off_before_on(self):
        sent = []
        project = Project(bpm=300, bars=1, loop_end=BAR, tracks=[Track('piano', clips=[Clip(length=BAR, notes=[
            Note(start=0, duration=96, pitch=60), Note(start=96, duration=96, pitch=60)])])])
        with worker(lambda data: sent.append(data) or True) as player:
            player.play(compile_plan(project, True, ensemble=True))
            self.assertTrue(player.wait_ready())
            wait_until(lambda: len(sent) >= 2)
            self.assertEqual(sent[1][1:5], b'\x0c\x3c\x01\0')
            self.assertEqual(sent[1][7:9], b'\x0c\x3c')
            self.assertEqual(sent[1][10], 1)

    def test_all_demo_wire_streams_match_with_batching(self):
        paths = sorted((Path(__file__).resolve().parents[2] / 'Music_Demos/projects').glob('*.tang.json'))
        self.assertEqual(len(paths), 32)
        for path in paths:
            with self.subTest(demo=path.name):
                plan = compile_plan(Project.load(path), True, ensemble=True)
                streams = []
                for batching in (False, True):
                    clock, sent = Clock(), []
                    player = ArrangementPlayer(lambda data: sent.append(data) or True,
                        clock.schedule, clock.cancel, clock=lambda: clock.now, batch_simultaneous=batching)
                    player.play(plan)
                    clock.advance(plan.duration + plan.preparation_seconds + 0.01)
                    self.assertEqual(player.state, 'stopped')
                    streams.append(b''.join(sent))
                self.assertEqual(*streams)

    def test_shutdown_rejects_new_work(self):
        player = ThreadedArrangementPlayer()
        self.assertTrue(player.shutdown())
        self.assertFalse(player.play(short_plan(False)))


class TransportTests(unittest.TestCase):
    def test_slow_write_fails_and_timeout_is_restored(self):
        port = MemoryPort()
        port.write_timeout = 2.0
        original = port.write
        def slow(data):
            self.assertEqual(port.write_timeout, 0.02)
            time.sleep(0.04)
            return original(data)
        port.write = slow
        sender = PlaybackSender(SerializedPort(port), timeout=0.02)
        with self.assertRaisesRegex(TimeoutError, '写入耗时'):
            sender(b'123456')
        self.assertEqual(port.write_timeout, 2)
        with self.assertRaises(IOError):
            sender(b'654321')
        self.assertEqual(len(port.writes), 1)

    def test_shared_lock_prevents_interleaved_writes_with_bounded_wait(self):
        port = SerializedPort(MemoryPort())
        entered, release = threading.Event(), threading.Event()
        def occupy():
            with port._write_lock:
                entered.set()
                release.wait(1)
        thread = threading.Thread(target=occupy)
        thread.start()
        self.assertTrue(entered.wait(1))
        try:
            with self.assertRaisesRegex(TimeoutError, '被其他任务占用'):
                port.write_bounded(b'123456', 0.02)
            self.assertFalse(port.writes)
        finally:
            release.set()
            thread.join(1)
        port.write_bounded(b'123456')
        self.assertEqual(port.writes, [b'123456'])

    def test_serial_exception_stops_future_events(self):
        port = MemoryPort()
        def broken(data):
            raise OSError('USB disconnected')
        port.write = broken
        with worker() as player:
            player.play(short_plan(), send=PlaybackSender(port))
            self.assertTrue(player.wait_ready())
            self.assertEqual(player.state, 'stopped')
            self.assertIn('USB disconnected', player.message)
            self.assertFalse(player.active)

    def test_slow_serial_success_is_not_allowed_to_catch_up_notes(self):
        port = MemoryPort()
        original = port.write
        def slow(data):
            time.sleep(0.04)
            return original(data)
        port.write = slow
        with worker() as player:
            player.play(short_plan(), send=PlaybackSender(port, timeout=0.02))
            self.assertTrue(player.wait_ready())
            self.assertEqual(player.state, 'stopped')
            self.assertIn('写入耗时', player.message)
            count = len(port.writes)
            time.sleep(0.12)
            self.assertEqual(len(port.writes), count)


class WorkerInterfaceTests(unittest.TestCase):
    application = interface_tests.ArrangementInterfaceTests.application

    def test_tk_stall_does_not_pause_serial_or_call_tk_from_worker(self):
        with self.application() as (app, panel):
            owner = threading.get_ident()
            original = panel._apply_controls
            def guarded(frames):
                self.assertEqual(threading.get_ident(), owner)
                original(frames)
            panel._apply_controls = guarded
            port = MemoryPort()
            app.port = port
            panel.hardware.set(True)
            panel.project.bpm = 300
            # Use production asynchronous callback, bypassing the old test adapter.
            ArrangementPanel.play(panel)
            self.assertTrue(panel.player.wait_ready())
            count = len(port.writes)
            time.sleep(0.4)
            self.assertGreater(len(port.writes), count)
            self.assertEqual(panel.player.state, 'playing', panel.player.message)
            panel._refresh_player()
            self.assertIn('最长迟到', panel.status.get())
            app.disconnect()
            self.assertFalse(port.is_open)
            self.assertEqual(panel.player.state, 'stopped')

    def test_rewind_stays_at_zero_and_destroy_joins_worker(self):
        with self.application() as (app, panel):
            panel.play()
            time.sleep(0.1)
            panel._refresh_player()
            self.assertGreater(panel.playhead, 0)
            panel.rewind()
            time.sleep(0.04)
            panel._refresh_player()
            self.assertEqual(panel.playhead, 0)
            thread = panel.player._thread
        self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()
