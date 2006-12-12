import sys

try:
    import numpy
except:
    print """Unable to import numpy.
    You need to install numpy (numpy.sf.net) in order to use PyGPU!""" 
    sys.exit(1)

try:
    import pygame
    from pygame.locals import *
except:
    print """Unable to import pygame.
    You need to install pygame (www.pygame.org) in order to use PyGPU!""" 
    sys.exit(1)

try:
    from pyglew import *
except:
    print """Unable to import pyglew.
    You need to install PyGLEW (www.cs.lth.se/~calle/pygpu2/) in order to use PyGPU!""" 
    sys.exit(1)

try:
    import Cg
except:
    print """Unable to import pycg.
    You need to install PyCG (www.cs.lth.se/~calle/pygpu2/) in order to use PyGPU!""" 
    sys.exit(1)

try:
    import PIL.Image
except:
    print """Unable to import PIL.
    You need to install Python Imaging Library (http://www.pythonware.com/products/pil/)!""" 
    sys.exit(1)


    

pygame.display.init()
surface = pygame.display.set_mode((512,512), OPENGL|DOUBLEBUF)

glewInit()

try:
    from pygpu import *
    from pygpu.functions import float2
    from pygpu.types import *
except:
    print """Unable to import pygpu.
    You need to install PyGPU (www.cs.lth.se/~calle/pygpu2/)!""" 
    sys.exit(1)

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
    kernel = numpy.array([[-1,-2,-1],
                          [0,0,0],
                          [1,2,1]])
    return sum([w*im(p+o) for w,o in zip(numpy.ravel(kernel),
                                         offsets(kernel))])**2

@gpu
def smooth(im=RGBImage, p=Position):
    kernel = numpy.array([[1,1,1],
                          [1,1,1],
                          [1,1,1]])
    return (1.0/9.0)*sum([w*im(p+o) for w,o in zip(numpy.ravel(kernel),
                                                   offsets(kernel))])

glDisable(GL_DEPTH_TEST)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 512, 0, 512, -1, 1)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

image = square()

while True:
    #check for quit'n events
    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

    glClear(GL_COLOR_BUFFER_BIT)

    image = smooth(image)
    image.show()
    
    pygame.display.flip()

