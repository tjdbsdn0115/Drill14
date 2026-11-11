from pico2d import open_canvas, close_canvas
import game_framework

import play_mode as start_mode

def main():
    open_canvas(1600, 600, sync=True)
    try:
        game_framework.run(start_mode)
    finally:
        close_canvas()


if __name__ == '__main__':
    main()

