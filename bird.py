"""The 14 painted poses in bird_animation.png, in reading order."""

from pico2d import load_image

FRAME_WIDTH = 182
FRAME_HEIGHT = 170
FRAME_COLUMNS = 5
FRAME_COUNT = 14  # The bottom-right cell is empty.
DRAW_WIDTH = 70
DRAW_SCALE = DRAW_WIDTH / FRAME_WIDTH
DRAW_HEIGHT = FRAME_HEIGHT * DRAW_SCALE


def frame_clip(frame, image_height):
    """Convert the atlas's top-left grid to pico2d's bottom-left clips."""
    index = int(frame) % FRAME_COUNT
    column, row = index % FRAME_COLUMNS, index // FRAME_COLUMNS
    top = row * FRAME_HEIGHT
    height = min(FRAME_HEIGHT, image_height - top)
    return column * FRAME_WIDTH, image_height - top - height, FRAME_WIDTH, height


class Bird:
    def __init__(self, image, x, y, direction=1):
        self.image = image
        self.x, self.y = x, y
        self.direction = direction
        self.frame = 0.0

    def update(self):
        pass

    def draw(self):
        left, bottom, width, height = frame_clip(self.frame, self.image.h)
        # The last row is 166px tall. Preserve the same top edge as a 170px cell.
        center_y = self.y + (FRAME_HEIGHT - height) * DRAW_SCALE / 2
        self.image.clip_composite_draw(
            left, bottom, width, height, 0,
            'h' if self.direction < 0 else '',
            self.x, center_y, DRAW_WIDTH, height * DRAW_SCALE,
        )
