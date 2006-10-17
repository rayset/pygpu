import sys, numpy

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


#@gpu
def f1(x=Int):
    if x < 0:
        x = 0
    return x

#@gpu
def f2(n=Int):
    x = 0
    for i in range(n):
        x += 1
    return x

def f3():
    x = 0
    for i in range(10):
        x += 1
    return x

#@gpu
def f4(x=Int):
    for i in range(10):
        x += i
    return x

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

@gpu
def convolve(im=RGBImage, p=Position):
    kernel = numpy.array([[-1,-sqrt(2),-1],
                          [0,0,0],
                          [1,sqrt(2),1]])
    return sum([w*im(p+o) for w,o in zip(numpy.ravel(kernel),
                                         offsets(kernel))])


@gpu(size = lambda x: (x.size[0]/2, x.size[1]/2))
def half(im=RGBImage, p=Position):
    return im(p*float2(2,2))

@gpu
def square(p=Position):
    x,y = p
    if (128.0 < x and x < 384.0) and\
       (128.0 < y and y < 384.0):
        res = float3(1,1,1)
    else:
        res = float3(0,0,0)
    return res

# @gpu(size = lambda x: x.size) ##(x.size[0], x.size))
# def columnSum(im=RGBImage, p=Position):
#     res = float3(0,0,0)
#     for i in range(512):
#         res += im(p + float2(0,i))
#     return res/float3(512, 512, 512)

# @gpu(size = lambda im,n: (512,512)) ##(x.size[0], x.size))
# def columnSumDynamic(im=RGBImage, n=Int, p=Position):
#     res = float3(0,0,0)
#     for i in range(n):
#         res += im(p + float2(0,i))
#     return res/float3(n,n,n)


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
    res = half(image)
    res.show()
    
    pygame.display.flip()

