from fractions import Fraction
import hashlib
import json
import unittest

from build_library import ROOT,neon
from demo_library import load_song,read_catalog
from time_machine_score import RIGHT,LEFT,SYSTEMS,BPM,EIGHTH_TICKS,hand_notes,warp
from time_machine_arrangement import compose_time_machine,short_time_machine,normalized_piano,source_tick
from arrangement_model import BAR,PPQ,Project
from arrangement_playback import ArrangementPlayer,compile_plan,score_notes
from test_arrangement import Clock
import test_arrangement_ui as interface_tests


class TimeMachineTests(unittest.TestCase):
    def test_all_72_printed_bars_and_both_hands_fit_six_eighths(self):
        self.assertEqual((len(RIGHT),len(LEFT)),(72,72))
        self.assertEqual([bar for page,system,first,last in SYSTEMS for bar in range(first,last+1)],list(range(1,73)))
        self.assertEqual((len(hand_notes('right')),len(hand_notes('left'))),(447,404))
        self.assertEqual((min(n['pitch'] for n in hand_notes('left')),max(n['pitch'] for n in hand_notes('right'))),(41,94))

    def test_sounding_octaves_and_explicit_naturals_are_preserved(self):
        right,left=hand_notes('right'),hand_notes('left')
        self.assertEqual([n['pitch'] for n in right[:3]],[77,82,87])
        self.assertTrue(any(n['pitch']==94 and n['source_bars']==[68] for n in right))
        self.assertTrue(any(n['pitch']==62 and n['source_bars']==[54] for n in right))
        self.assertTrue(any(n['pitch']==62 and n['source_bars']==[62] for n in right))
        self.assertTrue(any(n['pitch']==74 and n['source_bars']==[70] for n in left))

    def test_compound_meter_and_triplet_rounding_do_not_accumulate_drift(self):
        self.assertEqual(EIGHTH_TICKS*6,2*PPQ)
        self.assertEqual(source_tick(12),BAR)
        self.assertEqual(source_tick(Fraction(12)+Fraction(1,3))-source_tick(12),53)
        self.assertEqual(source_tick(18),3*PPQ*2)
        self.assertEqual(source_tick(432),146*PPQ)
        self.assertEqual(BPM,52)

    def test_ties_and_two_fermata_extensions_remain_held(self):
        right,left=hand_notes('right'),hand_notes('left')
        self.assertEqual(right[-1]['source_bars'],[71,72])
        self.assertTrue(any(n['source_bars']==[63,64] and n['pitch']==56 for n in left))
        self.assertEqual(warp(Fraction(378)),381)
        self.assertEqual(warp(Fraction(381)),387)
        self.assertEqual(warp(Fraction(432)),438)

    def test_same_pitch_gates_are_normalized_across_hands(self):
        notes=normalized_piano();groups={}
        for note in notes:groups.setdefault(note['pitch'],[]).append(note)
        for group in groups.values():
            for a,b in zip(group,group[1:]):self.assertLessEqual(a['end_tick'],b['start_tick'])
        project=compose_time_machine()
        actual={(c.start+n.start,n.pitch) for t in project.tracks[:2] for c in t.clips for n in c.notes}
        expected={(n['start_tick'],n['pitch']) for n in notes}
        self.assertEqual(actual,expected)

    def test_piano_leads_and_clean_guitar_is_the_only_accompanist(self):
        project=compose_time_machine();notes=score_notes(project)
        self.assertEqual([track.instrument for track in project.tracks],['piano','piano','guitar'])
        self.assertGreater(sum(n.instrument=='piano' for n in notes),sum(n.instrument=='guitar' for n in notes)*4)
        self.assertEqual(project.parameters['guitar.amp'],0)
        self.assertEqual(project.guitar_sustain,127)
        maxima={lane.target:max(p.value for p in lane.points) for lane in project.automation}
        self.assertEqual((maxima['bus.piano'],maxima['bus.guitar']),(36,66))
        self.assertEqual((maxima['bus.drums'],maxima['bus.bass'],maxima['bus.violin']),(0,0,0))
        sweep=source_tick(32*6+3)
        cluster=sorted(n.start-sweep for n in notes if n.instrument=='guitar' and sweep<=n.start<=sweep+28)
        self.assertEqual(cluster,[0,14,28])

    def test_neon_acoustic_settings_and_natural_envelope_are_restored_before_plucks(self):
        neon_project=Project.load(ROOT/'projects/06_neon_runway_full.tang.json')
        full=compose_time_machine()
        for score in (full,short_time_machine(full)):
            self.assertEqual(score.guitar_sustain,neon_project.guitar_sustain)
            self.assertEqual({k:v for k,v in score.parameters.items() if k.startswith('guitar.')},
                             {k:v for k,v in neon_project.parameters.items() if k.startswith('guitar.')})
            plan=compile_plan(score,True,ensemble=True)
            self.assertFalse(plan.preparation)
            reset=next(e for e in plan.events if e.data==bytes.fromhex('a5 13 00 00 00 b6'))
            first=next(e for e in plan.events if e.kind=='on' and e.note.instrument=='guitar')
            self.assertLess(plan.events.index(reset),plan.events.index(first))

    def test_piano_melody_stays_in_manual_single_key_velocity_bank(self):
        full=compose_time_machine()
        for project in (full,short_time_machine(full)):
            right=project.tracks[0]
            velocities=[round(n.velocity*right.level/100) for c in right.clips for n in c.notes]
            self.assertTrue(velocities)
            self.assertTrue(all(80<=v<112 for v in velocities))
            left=project.tracks[1]
            self.assertLess(max(round(n.velocity*left.level/100) for c in left.clips for n in c.notes),48)
            self.assertEqual(project.parameters['space.chorus_mix'],0)
            self.assertEqual(project.parameters['space.delay_mix'],0)

    def test_previous_30_projects_and_original_pdf_are_preserved(self):
        proof=json.loads((ROOT/'time_machine_validation.json').read_text(encoding='utf-8'))
        self.assertEqual(len(proof['previous_projects']),30)
        for name,sha in proof['previous_projects'].items():
            self.assertEqual(hashlib.sha256((ROOT/'projects'/name).read_bytes()).hexdigest(),sha)
        source=ROOT/proof['source_pdf']
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),proof['source_pdf_sha256'])
        self.assertTrue(proof['tempo_not_printed_in_source'])

    def test_saved_versions_are_reproducible_and_finish_without_stuck_keys(self):
        full=compose_time_machine()
        for variant,expected in (('full',full),('short',short_time_machine(full))):
            saved=Project.load(ROOT/'projects'/f'p07_time_machine_{variant}.tang.json')
            self.assertEqual(saved,expected)
            plan=compile_plan(saved,True,ensemble=True)
            self.assertAlmostEqual(plan.duration,(38 if variant=='full' else 8)*240/BPM)
            clock=Clock();sent=[]
            player=ArrangementPlayer(lambda data:sent.append(data) or True,clock.schedule,clock.cancel,clock=lambda:clock.now)
            player.play(plan);clock.advance(plan.duration+plan.preparation_seconds+.2)
            self.assertEqual(player.state,'stopped');self.assertFalse(player.active);self.assertFalse(clock.jobs)
            report=neon.analyze(saved)
            self.assertEqual(report['simultaneous_instrument_types'],2)
            self.assertLessEqual(report['gated_peak_voices']['piano'],16)
            self.assertLess(report['maximum_bytes_per_100ms'],400)

    def test_short_has_db_cadence_and_launchers_select_the_new_entry(self):
        short=short_time_machine(compose_time_machine())
        self.assertEqual({n.pitch for t in short.tracks[:2] for c in t.clips if c.start==6*BAR for n in c.notes},{49,56,61,65,68,73})
        self.assertFalse(any(n.start>=7*BAR for n in score_notes(short)))
        for name in ('打开TimeMachine钢琴吉他.cmd','打开TimeMachine短试听.cmd'):
            self.assertIn('-Song p07_time_machine',(ROOT.parent/name).read_text(encoding='ascii'))
        entry=next(song for song in read_catalog() if song['id']=='p07_time_machine')
        self.assertTrue(entry['piano_lead']);self.assertFalse(entry['original'])

    def test_hidden_ui_loads_both_versions_without_autoplay(self):
        harness=interface_tests.ArrangementInterfaceTests()
        with harness.application() as (app,panel):
            port=interface_tests.MemoryPort();app.port=port
            for variant in ('full','short'):
                self.assertTrue(load_song(app,'p07_time_machine',variant))
                self.assertFalse(panel.hardware.get())
                self.assertIn('Time Machine',panel.status.get())
                self.assertEqual(panel.project.bpm,52)
            self.assertFalse(port.writes)


if __name__=='__main__':unittest.main()
