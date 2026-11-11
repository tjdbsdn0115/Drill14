from pico2d import *

RULER_Y = 350

class Grass:
    # The red labels start 50px below the top of the 100px source image.
    label_top = RULER_Y

    def __init__(self):
        self.image = load_image('grass.png')
        self.ruler_image = load_image('ruler.png')

    def update(self):
        pass

    def draw(self):
        self.image.draw(400, 30)
        self.image.draw(1200, 30)
        self.ruler_image.draw(800, RULER_Y)


