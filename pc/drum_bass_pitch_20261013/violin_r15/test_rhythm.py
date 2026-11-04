from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from arrangement_model import BAR, PPQ, Clip, Note, Track, Project
from arrangement_playback import compile_plan
from arrangement_worker import ThreadedArrangementPlayer
from ensemble_protocol import targeted_note
from melody_player import command_frame
from rhythm_audio import LEAD_IN, LiveStriker, game_plan, strike_frames
from rhythm_input import HallInput
from rhythm_model import Chart, Target, Session, make_chart, training_project
from rhythm_panel import ResultStore


def chart_for(targets, radius=.05):
    return Chart('test', 'guitar', tuple(targets), 5, 120, '标准', 1.35, radius, 'test-sha', len(targets))


class ChartTests(unittest.TestCase):
    def test_training_score_and_all_difficulties_are_reproducible(self):
        project = training_project()
        before = project.to_dict()
        counts = []
        for difficulty in ('入门', '标准', '挑战'):
            chart = make_chart(project, project.tracks[0].id, difficulty)
            self.assertEqual(chart, make_chart(project, project.tracks[0].id, difficulty))
            self.assertTrue(any(target.slider for target in chart.targets))
            counts.append(len(chart.targets))
            self.assertTrue(compile_plan(project, True, ensemble=True))
        self.assertEqual(counts, sorted(counts))
        self.assertEqual(project.to_dict(), before)

    def test_slider_geometry_is_bounded_and_leaves_time_for_next_hit(self):
        project = training_project()
        chart = make_chart(project, project.tracks[0].id)
        for target, following in zip(chart.targets, chart.targets[1:]):
            self.assertLessEqual(target.at+target.duration, following.at-.19)
            for fraction in (0, .25, .5, .75, 1):
                x, y = target.position(fraction)
                self.assertTrue(.08 <= x <= .92 and .05 <= y <= .60)

    def test_chords_are_one_target_with_all_simultaneous_notes(self):
        project = training_project()
        chart = make_chart(project, project.tracks[1].id)
        self.assertEqual(len(chart.targets), 7)
        self.assertTrue(all(len(target.notes) == 3 for target in chart.targets))

    def test_hall_maps_have_no_sliders_and_preserve_string_mapping(self):
        project = training_project()
        chart = make_chart(project, project.tracks[0].id, sliders=False)
        self.assertFalse(any(target.slider for target in chart.targets))
        self.assertTrue(all(1 <= target.string <= 6 for target in chart.targets))

    def test_unknown_muted_and_empty_tracks_are_rejected(self):
        project = training_project()
        for key in ('missing', None):
            with self.assertRaises(ValueError):
                make_chart(project, key)
        project.tracks[0].muted = True
        with self.assertRaises(ValueError):
            make_chart(project, project.tracks[0].id)
        project.tracks[0].muted = False
        project.tracks[0].clips.clear()
        with self.assertRaises(ValueError):
            make_chart(project, project.tracks[0].id)

    def test_instrument_changes_have_distinct_record_fingerprints(self):
        project = training_project()
        before = make_chart(project, project.tracks[0].id)
        project.tracks[0].instrument = 'piano'
        after = make_chart(project, project.tracks[0].id)
        self.assertNotEqual(before.fingerprint, after.fingerprint)


class JudgementTests(unittest.TestCase):
    def test_early_late_window_boundaries_and_offset(self):
        for seconds, expected in ((0,300),(.045,300),(.0451,100),(.100,100),(.1001,50),(.160,50)):
            for sign in (1,-1):
                session = Session(chart_for([Target(0,1,.5,.3)]))
                hit = session.tap(1+sign*seconds, (.5,.3))
                self.assertEqual(hit.score, expected)
        session = Session(chart_for([Target(0,1,.5,.3)]), offset_ms=100)
        self.assertEqual(session.tap(1.1,(.5,.3)).score, 300)

    def test_aim_early_spam_and_repeat_do_not_award_extra_points(self):
        session = Session(chart_for([Target(0,1,.5,.3)]))
        self.assertIsNone(session.tap(.1,(.5,.3)))
        self.assertIsNone(session.tap(1,(.7,.3)))
        self.assertEqual(session.tap(1,(.5,.3)).score,300)
        self.assertIsNone(session.tap(1.01,(.5,.3)))
        self.assertEqual(session.combo,1)

    def test_hall_requires_matching_string_and_h1_is_wildcard(self):
        target=Target(0,1,.5,.3,string=6)
        session=Session(chart_for([target]),assist=True)
        self.assertIsNone(session.tap(1,string=1))
        self.assertEqual(session.tap(1,string=6).score,300)
        self.assertEqual(Session(chart_for([target]),assist=True).tap(1,string=0).score,300)

    def test_one_input_cannot_hit_two_chord_objects(self):
        session=Session(chart_for([Target(0,1,.5,.3),Target(1,1.02,.5,.3)]))
        session.tap(1,(.5,.3))
        self.assertEqual(len(session.done),1)

    def test_miss_expiry_combo_hp_and_accuracy(self):
        session=Session(chart_for([Target(0,1,.5,.3),Target(1,2,.5,.3)]))
        session.tap(1,(.5,.3))
        session.advance(3)
        self.assertEqual(session.combo,0)
        self.assertEqual(session.max_combo,1)
        self.assertEqual(session.accuracy,50)
        self.assertEqual(session.counts['MISS'],1)
        self.assertEqual(session.hp,92)

    def test_slider_must_be_held_and_followed_to_completion(self):
        target=Target(0,1,.25,.25,.8,(.45,.1),(.65,.35))
        for follows, expected in ((True,300),(False,0)):
            session=Session(chart_for([target]))
            self.assertEqual(session.tap(1,(target.x,target.y)).text,'HOLD')
            self.assertFalse(session.finished)
            for i in range(1,82):
                now=1+i*.01
                session.advance(now,target.position((now-1)/.8),pressed=follows)
            self.assertEqual(session.done[0].score,expected)

    def test_stalled_frame_cannot_fake_slider_tracking(self):
        target=Target(0,1,.25,.25,.8,(.45,.1),(.65,.35))
        session=Session(chart_for([target]))
        session.tap(1,(target.x,target.y))
        session.advance(1.81,target.tail,pressed=True)
        self.assertEqual(session.done[0].score,0)

    def test_autoplay_completes_training_and_is_marked_unranked(self):
        project=training_project();chart=make_chart(project,project.tracks[0].id)
        session=Session(chart,autoplay=True)
        self.assertIsNone(session.tap(0,(.5,.3)))
        for step in range(round((chart.duration+1)*100)):
            session.advance(step*.01)
        self.assertTrue(session.finished)
        self.assertEqual(session.accuracy,100)
        self.assertTrue(session.summary()['autoplay'])

    def test_backward_render_time_does_not_duplicate_judgements(self):
        session=Session(chart_for([Target(0,1,.5,.3)]))
        session.advance(2)
        session.advance(.5)
        self.assertEqual(len(session.done),1)


class HallInputTests(unittest.TestCase):
    def test_pick_strum_and_old_channel_mapping(self):
        adapter=HallInput()
        hit=adapter.feed('I (1000) HALL: PICK H2 string=6 velocity=92 queued=1',50)
        self.assertEqual((hit.string,hit.channel,hit.velocity),(6,2,92))
        strum=adapter.feed('I (1020) HALL: STRUM H1 strings=6,5,4,3,2,1 interval_ms=8 velocity=100 queued=1',50.025)
        self.assertEqual((strum.string,strum.channel),(0,1))
        self.assertAlmostEqual(strum.at,50.020)
        self.assertEqual(adapter.feed('I (1050) HALL: PICK H1 string=6 velocity=75 queued=0',50.05).string,6)

    def test_duplicates_snapshots_and_bad_values_are_not_hits(self):
        adapter=HallInput()
        line='I (1000) HALL: PICK H2 string=6 velocity=92 queued=1'
        self.assertIsNotNone(adapter.feed(line,50))
        self.assertIsNone(adapter.feed(line,50.01))
        for invalid in ('HALL,2,RAW,123,EVENTS,15','HALLDIAG,2,CAL,OK',
                        'I (2000) HALL: PICK H2 string=6 velocity=0 queued=1'):
            self.assertIsNone(adapter.feed(invalid,51))

    def test_stale_backlog_reboot_and_missing_timestamps(self):
        adapter=HallInput()
        adapter.feed('I (10000) HALL: PICK H2 string=6 velocity=90 queued=1',50)
        self.assertIsNone(adapter.feed('I (10100) HALL: PICK H2 string=6 velocity=90 queued=1',51))
        self.assertIsNotNone(adapter.feed('I (10) HALL: PICK H2 string=6 velocity=90 queued=1',52))
        hit=adapter.feed('HALL: PICK H2 string=6 velocity=90 queued=1',53)
        self.assertFalse(hit.timestamped)
        self.assertEqual(hit.at,53)


class AudioTests(unittest.TestCase):
    def test_follow_plan_countin_preserves_music_and_setup(self):
        project=training_project()
        base=compile_plan(project,True,ensemble=True)
        plan=game_plan(project,'guitar',True,False)
        self.assertEqual(plan.duration,base.duration+LEAD_IN)
        self.assertEqual([event.data for event in plan.events],[event.data for event in base.events])
        for before,after in zip(base.events,plan.events):
            self.assertAlmostEqual(after.at,before.at+(LEAD_IN if before.kind in ('on','off') or before.at>0 else 0))

    def test_performance_mutes_all_target_instrument_tracks_and_retains_effects(self):
        project=training_project();before=project.to_dict()
        clone=deepcopy(project.tracks[0]);clone.id='second-guitar'
        for clip in clone.clips:
            clip.id+='-copy'
            for note in clip.notes:note.id+='-copy'
        project.tracks.append(clone)
        plan=game_plan(project,'guitar',True,True)
        self.assertFalse(any(event.note.instrument=='guitar' for event in plan.events if event.kind=='on'))
        self.assertEqual({event.note.instrument for event in plan.events if event.kind=='on'},{'piano','bass','drums'})
        self.assertTrue(plan.preparation)
        project.tracks.pop()
        self.assertEqual(project.to_dict(),before)
        with self.assertRaises(ValueError):game_plan(project,'piano',True,True)

    def test_live_packets_only_use_existing_instrument_opcodes(self):
        project=training_project()
        for index,opcode in ((0,0x0a),(3,0x50)):
            target=make_chart(project,project.tracks[index].id).targets[0]
            packet=strike_frames(target,project.tracks[index].instrument)
            for offset in range(0,len(packet),6):
                frame=packet[offset:offset+6]
                self.assertEqual(frame[1],opcode)
                checksum=0
                for value in frame:checksum^=value
                self.assertEqual(checksum,0)

    def test_live_writer_runs_outside_ui_and_latches_failure(self):
        sent=[];done=threading.Event()
        def sender(data):
            sent.append((threading.current_thread().name,data));done.set();return True
        writer=LiveStriker(sender)
        packet=targeted_note('guitar',64,90,True)
        try:
            self.assertTrue(writer.submit(packet));self.assertTrue(done.wait(1))
            self.assertEqual(sent[0][0],'RhythmLiveHits')
            with self.assertRaises(ValueError):writer.submit(command_frame(0x0c,60,90,1))
        finally:self.assertTrue(writer.shutdown())
        self.assertFalse(writer.submit(packet))
        failed=LiveStriker(lambda data:False)
        failed.submit(packet)
        deadline=time.monotonic()+1
        while not failed.error and time.monotonic()<deadline:time.sleep(.005)
        self.assertTrue(failed.error)
        self.assertFalse(failed.submit(packet));failed.shutdown()

    def test_worker_snapshots_export_clock_without_using_tk_timers(self):
        project=training_project()
        worker=ThreadedArrangementPlayer(lambda data:True)
        try:
            worker.play(game_plan(project,'guitar',False,False))
            self.assertTrue(worker.wait_ready(1))
            snapshot=worker.snapshot()
            self.assertGreater(snapshot.published_at,0)
            self.assertFalse(snapshot.preparing)
            self.assertEqual(snapshot.state,'playing')
            worker.stop();self.assertTrue(worker.wait_ready(1))
        finally:self.assertTrue(worker.shutdown())


class RecordTests(unittest.TestCase):
    def test_only_complete_non_demo_records_are_persisted_and_profiles_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            store=ResultStore(Path(directory)/'best.json')
            summary={'chart_sha256':'x','score':300,'accuracy':100,'max_combo':1,'counts':{'PERFECT':1},'objects':1,'judged':1,'autoplay':False}
            self.assertFalse(store.record({**summary,'autoplay':True},'mouse'))
            self.assertFalse(store.record({**summary,'judged':0},'mouse'))
            self.assertTrue(store.record(summary,'mouse'))
            self.assertFalse(store.record({**summary,'score':100},'mouse'))
            self.assertTrue(store.record(summary,'hall'))
            self.assertEqual(len(json.loads(store.path.read_text(encoding='utf-8'))),2)
            self.assertFalse(store.path.with_suffix('.tmp').exists())


if __name__=='__main__':
    unittest.main()
