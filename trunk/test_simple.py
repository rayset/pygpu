import sys

import pygame
from pygame.locals import *
from pyglew import *

w,h = 512,512

pygame.display.init()
surface = pygame.display.set_mode((w,h), OPENGL|DOUBLEBUF)

glewInit()

from pygpu import *
from pygpu.functions import float2
from pygpu.types import *

initPyGPU()


@gpu(size = lambda *args: (w,h))
def simple(p=Position):
    return float3(1,0,0)

glDisable(GL_DEPTH_TEST)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, w, 0, h, -1, 1)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

while True:
    #check for quit'n events
    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

    glClear(GL_COLOR_BUFFER_BIT)

    res = simple()
    res.show()

    

    pygame.display.flip()

