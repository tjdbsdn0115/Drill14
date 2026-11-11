"""Ten time-based birds using the atlas's 14 poses in reading order.

See docs/BIRD_FLIGHT.md for measured atlas boundaries, reflected travel,
formation offsets, numeric-label clearance, and verification evidence.
"""

from pico2d import load_image
import game_framework

FRAME_WIDTH = 182
FRAME_HEIGHT = 170
FRAME_COLUMNS = 5
FRAME_COUNT = 14  # The bottom-right cell is empty.
DRAW_WIDTH = 70
DRAW_SCALE = DRAW_WIDTH / FRAME_WIDTH
DRAW_HEIGHT = FRAME_HEIGHT * DRAW_SCALE
WINGBEATS_PER_SECOND = 2.0
FRAMES_PER_SECOND = FRAME_COUNT * WINGBEATS_PER_SECOND
PIXEL_PER_METER = 10.0 / 0.3  # Same world scale as boy.py.
FLIGHT_SPEED_KMPH = 30.0
FLIGHT_SPEED_PPS = FLIGHT_SPEED_KMPH * 1000.0 / 3600.0 * PIXEL_PER_METER
FLOCK_SIZE = 10
FLOCK_COLUMNS = 5
HORIZONTAL_SPACING = 130
VERTICAL_SPACING = 72
MESSAGE_CLEARANCE = 16


def frame_clip(frame, image_height):
    """Convert the atlas's top-left grid to pico2d's bottom-left clips."""
    index = int(frame) % FRAME_COUNT
    column, row = index % FRAME_COLUMNS, index // FRAME_COLUMNS
    top = row * FRAME_HEIGHT
    height = min(FRAME_HEIGHT, image_height - top)
    return column * FRAME_WIDTH, image_height - top - height, FRAME_WIDTH, height


def reflected_motion(x, direction, distance, left, right):
    """Reflect all overshoot, even when one update crosses several walls."""
    span = right - left
    if span <= 0:
        return left, direction
    phase = x - left if direction > 0 else 2 * span - (x - left)
    phase = (phase + distance) % (2 * span)
    if phase < span:
        return left + phase, 1
    return right - (phase - span), -1


class Bird:
    """A shared-texture bird with independent wing phase and translated patrol."""

    def __init__(self, image, x, y, direction=1, phase=0.0,
                 bounds=(DRAW_WIDTH / 2, 1600 - DRAW_WIDTH / 2)):
        self.image = image
        self.x, self.y = x, y
        self.direction = direction
        self.frame = phase % FRAME_COUNT
        self.left, self.right = bounds

    def update(self, dt=None):
        if dt is None:
            dt = game_framework.frame_time
        self.frame = (self.frame + FRAMES_PER_SECOND * dt) % FRAME_COUNT
        self.x, self.direction = reflected_motion(
            self.x, self.direction, FLIGHT_SPEED_PPS * dt, self.left, self.right,
        )

    def draw(self):
        left, bottom, width, height = frame_clip(self.frame, self.image.h)
        # The last row is 166px tall. Preserve the same top edge as a 170px cell.
        center_y = self.y + (FRAME_HEIGHT - height) * DRAW_SCALE / 2
        self.image.clip_composite_draw(
            left, bottom, width, height, 0,
            'h' if self.direction < 0 else '',
            self.x, center_y, DRAW_WIDTH, height * DRAW_SCALE,
        )


def create_flock(canvas_width, boy, label_top=0):
    """Load one texture for ten birds; translated bounds keep their formation."""
    image = load_image('bird_animation.png')
    base_y = max(boy.visual_top, label_top) + MESSAGE_CLEARANCE + DRAW_HEIGHT / 2
    # Fit the formation if the canvas is narrower than the default 1600px.
    spacing = min(HORIZONTAL_SPACING,
                  max(0, (canvas_width - DRAW_WIDTH) / (FLOCK_COLUMNS - 1)))
    half_span = spacing * (FLOCK_COLUMNS - 1) / 2
    group_left = DRAW_WIDTH / 2 + half_span
    group_right = canvas_width - DRAW_WIDTH / 2 - half_span
    start = (group_left + group_right) / 2
    birds = []
    for index in range(FLOCK_SIZE):
        column, row = index % FLOCK_COLUMNS, index // FLOCK_COLUMNS
        offset = column * spacing - half_span
        # Equal patrol lengths and equal relative starts synchronize all turns.
        birds.append(Bird(
            image, start + offset, base_y + row * VERTICAL_SPACING,
            phase=index * FRAME_COUNT / FLOCK_SIZE,
            bounds=(group_left + offset, group_right + offset),
        ))
    return birds
