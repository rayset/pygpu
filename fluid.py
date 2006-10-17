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

crossSamples = numpy.array([(1,0), (-1,0), (0,1), (0,-1)]) 

## @gpu
def divergence(x,p):
    r,l,t,b = [x(p+o) for o in crossSamples]
    return r[0] + t[1] - l[0] - b[1]

@gpu(size = lambda dx,x: x.size)
def myDiv(dx=Float, x=RGBImage, p=Position):
    p = round(p)
    return 0.5*divergence(x,p)/dx


def bilerp(im, p):
    minX = floor(p[0])
    minY = floor(p[1])
    maxX = minX+1
    maxY = minY+1

    fracX = frac(p[0])
    fracY = frac(p[1])

    ll = im(float2(minX, minY))
    lr = im(float2(maxX, minY))
    ul = im(float2(minX, maxY))
    ur = im(float2(maxX, maxY))

    return lerp(lerp(ll, lr, fracX), 
                lerp(ul, ur, fracX),  
                fracY)


@gpu
def transport(dt=Float, vectorField=RGBImage, src=RGBImage, p=Position):
    ## pfrac = frac(p)
    p -= frac(p) + dt*vectorField(p)[0:2]
    return bilerp(src, p)

## @gpu
def gradient(x=RGBImage, p=Position):
    r,l,t,b = [x(p+o)[0] for o in crossSamples]
    return float3(r-l, t-b, 0)

@gpu
def solvePoisson(alpha=Float, beta=Float, x=RGBImage, b=RGBImage, p=Position):
    samples = [x(p+o) for o in crossSamples]
    return (sum(samples) + alpha*b(p))/beta

@gpu
def gradientSubtract(dx=Float, x=RGBImage, w=RGBImage, p=Position):
    return w(p) - 0.5*gradient(x,p)/dx

def solveLHS(alpha, beta, x, b, iterations=20):
    for i in xrange(iterations):
        x = solvePoisson(alpha, beta, x, b)
        return x

def solveRHS(alpha, beta, x, b, iterations=10):
    for i in xrange(iterations):
        b = solvePoisson(alpha, beta, x, b)
    return b

def fluidStep(v, p, dt=0.1, dx=0.1, visc=0.2):
    ## Transport velocity along the velocity field
    v = transport(dt, v, v)

    ## solve for viscous diffusion
    alpha = dx*dx/(visc*dt)
    v = solveRHS(alpha, 4+alpha, v, v)
    
    ## solve poisson pressure equation
    # start guessing with a all-zero image (None)
    x = solveLHS(-dx*dx, 4, None, myDiv(dx,v))

    ## subtract the gradient of x from v
    v = gradientSubtract(dx, x, v)

    ## transport pressure along the velocity field.
    p = transport(dt, v, p)

    return v, p

@gpu
def absIm(im=RGBImage, p=Position):
    return abs(im(p))



p = loadImage("data/pressure.bmp", RGBImage)
v = loadImage("data/velocity.bmp", RGBImage)

glDisable(GL_DEPTH_TEST)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 512, 0, 512, -1, 1)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()


clock = pygame.time.Clock()

while True:
    #check for quit'n events
    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

    clock.tick()

    glClear(GL_COLOR_BUFFER_BIT)

    #v,p = fluidStep(v,p)
    #p.show()
    #p.show()
    dt = 0.5 ##clock.get_time()/1000.0
    if dt > 0.0:
        v,p = fluidStep(v, p, dt)
        p.show()
#    print "FPS:", clock.get_fps()
    #    res = myDiv(0.1, p)
    #    res.show()

    ##    
    
    pygame.display.flip()

