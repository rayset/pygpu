import sys

import pygame
from pygame.locals import *
from pyglew import *

pygame.display.init()
surface = pygame.display.set_mode((512,512), OPENGL|DOUBLEBUF)

glewInit()

from pygpu import *
from pygpu.functions import float2
from pygpu.types import *

initPyGPU()

@gpu(size = lambda *args: (512,512))
def square(p=Position):
    x,y = p
    if (128.0 < x and x < 384.0) and\
       (128.0 < y and y < 384.0):
        res = float3(1,1,1)
    else:
        res = float3(0,0,0)
    return res

glDisable(GL_DEPTH_TEST)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 512, 0, 512, -1, 1)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

while True:
    #check for quit'n events
    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

    glClear(GL_COLOR_BUFFER_BIT)

    #    res = columnSumDynamic(image,100)
    res = square()
    print res
    res.show()
    
    pygame.display.flip()

