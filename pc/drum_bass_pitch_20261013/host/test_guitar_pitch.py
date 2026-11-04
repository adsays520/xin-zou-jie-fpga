import math
import unittest
from dataclasses import replace
from unittest.mock import patch
from guitar_pitch import PitchControl, PitchSettings
from guitar_controller import GuitarController, TIMBRE_BASS, TIMBRE_GUITAR
from test_embedded_pages import Port


class PitchMathTests(unittest.TestCase):
    def model(self, **settings):
        return PitchControl(PitchSettings(**settings), clock=lambda: 0)

    def test_slide_is_continuous_monotonic_and_exact_at_endpoint(self):
        model = self.model(slide_range_cents=1200, slide_ms=1000)
        model.set_slide_position(1, now=0)
        values = [model.snapshot(440, t / 100)['frequency_hz'] for t in range(101)]
        self.assertEqual(values[0], 440)
        self.assertEqual(values[-1], 880)
        self.assertEqual(values, sorted(values))
        model.set_slide_position(-1, now=1)
        self.assertEqual(model.snapshot(440, 1)['frequency_hz'], 880)
        self.assertEqual(model.snapshot(440, 2)['frequency_hz'], 220)

    def test_retarget_has_no_pitch_jump_and_return_reaches_zero(self):
        model = self.model(slide_ms=500)
        model.set_slide_position(1, now=0)
        before = model.advance(.2)
        model.set_slide_position(-1, now=.2)
        self.assertEqual(model.advance(.2), before)
        model.set_slide_position(0, now=.3)
        self.assertEqual(model.advance(.8), 0)

    def test_vibrato_period_and_depth_and_smooth_disable(self):
        model = self.model(vibrato_rate_hz=5, vibrato_depth_cents=100)
        model.enable_vibrato(True, now=0)
        self.assertAlmostEqual(model.advance(.05), 100)
        self.assertAlmostEqual(model.advance(.15), -100)
        self.assertAlmostEqual(model.advance(.25), 100)
        model.enable_vibrato(False, now=.25)
        self.assertAlmostEqual(model.advance(.25), 100)
        self.assertEqual(model.advance(.27), 0)

    def test_encoder_clamps_both_directions_and_supports_fine_steps(self):
        model = self.model()
        self.assertEqual(model.handle_encoder_delta('slide_range_cents', 1, now=0), 225)
        self.assertEqual(model.handle_encoder_delta('slide_range_cents', -1, fine=True, now=0), 220)
        self.assertEqual(model.handle_encoder_delta('slide_range_cents', 10000, now=0), 1200)
        self.assertEqual(model.handle_encoder_delta('slide_range_cents', -10000, now=0), 0)
        self.assertEqual(model.handle_encoder_delta('vibrato_rate_hz', -10000, now=0), .5)
        self.assertEqual(model.handle_encoder_delta('vibrato_rate_hz', 10000, now=0), 12)
        for field, detents in [('invalid', 1), ('slide_ms', .5), ('slide_ms', True)]:
            with self.assertRaises(ValueError): model.handle_encoder_delta(field, detents)

    def test_rate_change_keeps_phase_and_invalid_settings_are_atomic(self):
        model = self.model()
        model.enable_vibrato(True, now=0)
        before = model.advance(.05)
        model.set_settings(replace(model.settings, vibrato_rate_hz=10), now=.05)
        self.assertAlmostEqual(model.advance(.05), before)
        settings = model.settings
        with self.assertRaises(ValueError):
            model.set_settings(replace(settings, slide_ms=float('nan')), now=.1)
        self.assertEqual(model.settings, settings)

    def test_combined_bounds_export_import_and_reset(self):
        model = self.model(slide_range_cents=1200, vibrato_depth_cents=200)
        model.set_slide_position(1, now=0)
        model.enable_vibrato(True, now=0)
        lo, hi = model.frequency_bounds(440)
        for t in range(401):
            hz = model.snapshot(440, t / 100)['frequency_hz']
            self.assertLessEqual(hz, hi)
            self.assertGreaterEqual(hz, lo)
        self.assertEqual(PitchSettings.from_dict(model.settings.to_dict()), model.settings)
        with self.assertRaises(ValueError): PitchSettings.from_dict({'version': 2})
        model.reset(now=4)
        self.assertEqual(model.snapshot(440, 5)['ratio_q20'], 1 << 20)
        self.assertFalse(model.vibrato_enabled)
        self.assertEqual(model.settings.slide_range_cents, 1200)


class PitchUiTests(unittest.TestCase):
    def test_preview_encoder_navigation_and_timbre_reset_do_not_send_pitch_frames(self):
        with patch.object(GuitarController, 'refresh_ports'):
            app = GuitarController()
        app.withdraw()
        port = Port()
        app.port = port
        errors = []
        app.report_callback_exception = lambda *args: errors.append(args)
        try:
            page = app.show_page('pitch')
            page.encoder(1)
            self.assertEqual(app.pitch_control.settings.slide_range_cents, 225)
            page.slide(1)
            page.vibrato.set(True)
            page.toggle_vibrato()
            app.update()
            self.assertEqual(port.data, [])
            self.assertIn('Hz', page.live.get())
            app.show_page('drums')
            self.assertIs(app.show_page('pitch'), page)
            app.send_timbre(TIMBRE_BASS)
            self.assertFalse(app.pitch_control.vibrato_enabled)
            self.assertEqual(page.position.get(), 0)
            page.slide(1)
            self.assertIn('请选择木吉他', page.status.get())
            app.send_timbre(TIMBRE_GUITAR)
            page.slide(-1)
            app.disconnect()
            self.assertEqual(app.pitch_control.advance(), 0)
            self.assertEqual(page.position.get(), 0)
            self.assertEqual(errors, [])
        finally:
            app.close()


if __name__ == '__main__':
    unittest.main()
