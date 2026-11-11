"""Exercise the real SDL renderer and export both flight directions for review."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pico2d
import pico2d.pico2d as engine
from sdl2 import (SDL_CreateRGBSurfaceWithFormat, SDL_FreeSurface,
                  SDL_PIXELFORMAT_RGBA32, SDL_RenderReadPixels)
from sdl2.sdlimage import IMG_SavePNG

import game_framework
import game_world
import play_mode
from bird import FRAME_COUNT, frame_clip


def save_frame(path):
    surface = SDL_CreateRGBSurfaceWithFormat(0, 1600, 600, 32, SDL_PIXELFORMAT_RGBA32)
    if not surface:
        raise RuntimeError('Could not allocate the review surface')
    try:
        result = SDL_RenderReadPixels(engine.renderer, None, SDL_PIXELFORMAT_RGBA32,
                                      surface.contents.pixels, surface.contents.pitch)
        if result != 0 or IMG_SavePNG(surface, str(path).encode('utf-8')) != 0:
            raise RuntimeError('Could not export the rendered frame')
    finally:
        SDL_FreeSurface(surface)


def main():
    output = ROOT / 'artifacts'
    output.mkdir(exist_ok=True)
    pico2d.open_canvas(1600, 600)
    try:
        play_mode.init()
        for name, dt, expected_direction in [('right', 0.0, 1), ('left', 2.0, -1)]:
            game_framework.frame_time = dt
            play_mode.update()
            assert len(play_mode.birds) == 10
            assert all(b.direction == expected_direction for b in play_mode.birds)
            pico2d.clear_canvas()
            game_world.render()
            save_frame(output / f'flock_{name}.png')
            pico2d.update_canvas()

        # Render all 14 real poses at one fixed row for visual clip inspection.
        pico2d.clear_canvas()
        image = play_mode.birds[0].image
        for index in range(FRAME_COUNT):
            left, bottom, width, height = frame_clip(index, image.h)
            image.clip_draw(left, bottom, width, height,
                            100 + (index % 7) * 220, 440 - (index // 7) * 270,
                            width, height)
        save_frame(output / 'all_14_poses.png')
        print('Real SDL render passed: 10 birds, both directions, all 14 poses.')
        print(f'Review images: {output}')
    finally:
        play_mode.finish()
        pico2d.close_canvas()


if __name__ == '__main__':
    main()
