import numpy

import pygame
from pygame.locals import *
from pyglew import *

pygame.display.init()
surface = pygame.display.set_mode((512,512), OPENGL|DOUBLEBUF)

glewInit()

from pygpu import *
from pygpu.types import *

initPyGPU()

array = numpy.ones((512,512,4), numpy.float32)
image = imageFromArray(array)

glDisable(GL_DEPTH_TEST)


glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 512, 0, 512, -1, 1)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

@gpu
def f(im=RGBAImage, p=Position):
    return float4(p[0]/512.0, p[1]/512.0, 1, 1)*im(p)

while True:
    #check for quit'n events
    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

    glClear(GL_COLOR_BUFFER_BIT)

    res = f(image)
    res.show()
    
    pygame.display.flip()
