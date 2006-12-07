
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

def offsets(kernel):
    n,m = numpy.shape(kernel)

    assert (n%2) == 1
    assert (m%2) == 1

    cx,cy = int(numpy.floor(n/2)),int(numpy.floor(m/2))

    yStart,yEnd = cy-m+1,m-cy
    xStart,xEnd = cx-n+1,n-cx

    return [numpy.array([i,j])
            for j in reversed(range(yStart, yEnd))
            for i in range(xStart, xEnd)]

def convolve(kernel, im=RGBImage, p=Position):
    return sum([w*im(p+o) for w,o in zip(numpy.ravel(kernel),
                                         offsets(kernel))])

@gpu
def isotropicEdge(im=RGBImage, p=Position):
    kY = numpy.array([[-1,-sqrt(2),-1],
                      [0,0,0],
                      [1,sqrt(2),1]])
    kX = numpy.transpose(kY)
    
    sX = convolve(kX, im, p)
    sY = convolve(kY, im, p)

    return sqrt(sX**2 + sY**2)


print isotropicEdge.func._getSource()

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

    #res = columnSumDynamic(image,10)
    res = isotropicEdge(image)
    res.show()
    
    pygame.display.flip()

