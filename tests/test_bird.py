import math
import struct
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bird
import game_framework
import game_world
import play_mode
from boy import Boy


class BirdTests(unittest.TestCase):
    def setUp(self):
        self.image = Mock(h=506)
        self.boy = SimpleNamespace(visual_top=148)

    def flock(self, width=1600):
        with patch('bird.load_image', return_value=self.image) as load:
            birds = bird.create_flock(width, self.boy, label_top=350)
        load.assert_called_once_with('bird_animation.png')
        return birds

    def test_atlas_dimensions_and_all_14_clips_stay_inside_the_real_png(self):
        with open('bird_animation.png', 'rb') as atlas:
            header = atlas.read(24)
        width, height = struct.unpack('>II', header[16:24])
        self.assertEqual((width, height), (918, 506))
        clips = [bird.frame_clip(i, height) for i in range(14)]
        self.assertEqual(len(set(clips)), 14)
        self.assertEqual(clips[0], (0, 336, 182, 170))
        self.assertEqual(clips[5], (0, 166, 182, 170))
        self.assertEqual(clips[-1], (546, 0, 182, 166))
        for left, bottom, w, h in clips:
            self.assertTrue(0 <= left < left + w <= width)
            self.assertTrue(0 <= bottom < bottom + h <= height)
        self.assertEqual(bird.frame_clip(14, height), clips[0])

    def test_last_row_keeps_the_same_destination_top_edge(self):
        b = bird.Bird(self.image, 400, 200)
        tops = []
        for frame in (0, 5, 10, 13):
            b.frame = frame
            b.draw()
            args = self.image.clip_composite_draw.call_args.args
            tops.append(args[7] + args[9] / 2)
        for top in tops:
            self.assertAlmostEqual(top, 200 + bird.DRAW_HEIGHT / 2)

    def test_left_flight_mirrors_pose_without_reversing_animation(self):
        b = bird.Bird(self.image, 400, 200, direction=-1, phase=4)
        b.update(1 / bird.FRAMES_PER_SECOND)
        b.draw()
        args = self.image.clip_composite_draw.call_args.args
        self.assertEqual(args[:4], bird.frame_clip(5, 506))
        self.assertEqual(args[5], 'h')

    def test_two_wingbeats_per_second_and_no_empty_cell(self):
        b = bird.Bird(self.image, 400, 200, phase=3)
        b.update(0.5)
        self.assertAlmostEqual(b.frame, 3)
        poses = set()
        for _ in range(140):
            poses.add(int(b.frame))
            b.update(1 / bird.FRAMES_PER_SECOND)
        self.assertEqual(poses, set(range(14)))

    def test_speed_matches_30_kmph_at_the_boy_world_scale(self):
        b = bird.Bird(self.image, 400, 200)
        b.update(0.25)
        self.assertAlmostEqual(b.x - 400, (30 / 3.6) * (10 / 0.3) * 0.25)

    def test_overshoot_and_exact_boundary_direction(self):
        self.assertEqual(bird.reflected_motion(90, 1, 25, 0, 100), (85, -1))
        self.assertEqual(bird.reflected_motion(10, -1, 25, 0, 100), (15, 1))
        self.assertEqual(bird.reflected_motion(90, 1, 10, 0, 100), (100, -1))
        self.assertEqual(bird.reflected_motion(10, -1, 10, 0, 100), (0, 1))

    def test_single_large_update_preserves_many_round_trips(self):
        self.assertEqual(bird.reflected_motion(25, 1, 10**9 + 120, 0, 100),
                         (55, -1))
        self.assertEqual(bird.reflected_motion(35, 1, 100, 35, 35), (35, 1))

    def test_equal_elapsed_time_at_30_60_144_fps_and_a_long_stall(self):
        reference = bird.Bird(self.image, 400, 200, phase=2.3)
        reference.update(19.125)
        for fps in (30, 60, 144):
            b = bird.Bird(self.image, 400, 200, phase=2.3)
            for _ in range(fps * 19):
                b.update(1 / fps)
            b.update(0.125)
            self.assertAlmostEqual(b.x, reference.x, places=7)
            self.assertEqual(b.direction, reference.direction)
            self.assertAlmostEqual(b.frame, reference.frame, places=7)

    def test_ten_birds_share_one_texture_with_distinct_wing_phases(self):
        flock = self.flock()
        self.assertEqual(len(flock), 10)
        self.assertEqual(len({b.frame for b in flock}), 10)
        self.assertTrue(all(b.image is self.image for b in flock))

    def test_formation_and_screen_bounds_survive_repeated_turns(self):
        for width in (800, 1600):
            flock = self.flock(width)
            offsets = [b.x - flock[0].x for b in flock]
            directions = set()
            for _ in range(1200):
                for b in flock:
                    b.update(1 / 30)
                    self.assertGreaterEqual(b.x - bird.DRAW_WIDTH / 2, -1e-8)
                    self.assertLessEqual(b.x + bird.DRAW_WIDTH / 2, width + 1e-8)
                directions.add(flock[0].direction)
                self.assertEqual(len({b.direction for b in flock}), 1)
                for b, offset in zip(flock, offsets):
                    self.assertAlmostEqual(b.x - flock[0].x, offset)
            self.assertEqual(directions, {-1, 1})

    def test_birds_clear_boy_message_and_each_other_vertically(self):
        actual_boy = Boy.__new__(Boy)
        actual_boy.y = 90
        self.assertEqual(actual_boy.visual_top, 148)
        flock = self.flock()
        self.assertAlmostEqual(min(b.y - bird.DRAW_HEIGHT / 2 for b in flock),
                               max(actual_boy.visual_top, 350) + 16)
        self.assertGreater(bird.VERTICAL_SPACING, bird.DRAW_HEIGHT)
        self.assertLess(max(b.y + bird.DRAW_HEIGHT / 2 for b in flock), 600)

    def test_mode_registers_ten_birds_and_clears_them_on_exit(self):
        game_world.clear()
        try:
            with patch('play_mode.Boy', return_value=self.boy), \
                    patch('play_mode.Grass', return_value=SimpleNamespace(label_top=350)), \
                    patch('play_mode.get_canvas_width', return_value=1600), \
                    patch('bird.load_image', return_value=self.image):
                play_mode.init()
            self.assertEqual(len(play_mode.birds), 10)
            self.assertEqual(sum(isinstance(o, bird.Bird)
                                 for layer in game_world.world for o in layer), 10)
            play_mode.finish()
            self.assertEqual(play_mode.birds, [])
            self.assertIsNone(play_mode.boy)
            self.assertFalse(any(game_world.world))
        finally:
            game_world.clear()


class FrameworkTests(unittest.TestCase):
    def test_current_delta_is_available_before_update_and_quit_skips_update(self):
        mode = Mock()
        observed = []
        def handle_events():
            if observed:
                game_framework.quit()
        mode.handle_events.side_effect = handle_events
        mode.update.side_effect = lambda: observed.append(game_framework.frame_time)
        with patch('game_framework.time.perf_counter', side_effect=[100.0, 100.025]):
            game_framework.run(mode)
        self.assertEqual(len(observed), 1)
        self.assertTrue(math.isclose(observed[0], 0.025))
        mode.finish.assert_called_once()
        self.assertFalse(game_framework.stack)


if __name__ == '__main__':
    unittest.main()
