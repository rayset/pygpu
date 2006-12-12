import sys, numpy
from pygpu import *
from pygpu.types import *


import pygame
from pygame.locals import *
from pyglew import *

pygame.display.init()
surface = pygame.display.set_mode((512,512), OPENGL|DOUBLEBUF)

glewInit()

initPyGPU()


@gpu(size = lambda x: x.size) ##(x.size[0], x.size))
def columnSum(im=RImage, p=Int):
    return im(p)

@gpu(size = lambda im,n: (512,512)) ##(x.size[0], x.size))
def columnSumDynamic(im=RGBImage, n=Int, p=Position):
    res = float3(0,0,0)
    for i in range(n):
        res += im(p + float2(0,i))
    return res/float3(n,n,n)


image = loadImage("data/naomi.jpg", RGBImage)

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

    res = columnSumDynamic(image,100)
    print res
    res.show()
    
    pygame.display.flip()

