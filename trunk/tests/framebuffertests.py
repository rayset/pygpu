
import unittest
import sys, numpy

sys.path.append('..')

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


@gpu(size=lambda s,colorX,colorY: s)
def fillGradient(size=Float2, cX=Float3, cY=Float3, p=Position):
    s,t = p/size
    return s*cX + t*cY

glDisable(GL_DEPTH_TEST)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 512, 0, 512, -1, 1)

glMatrixMode(GL_MODELVIEW)
glLoadIdentity()




class FramebufferTestCase(unittest.TestCase):

    def runTest(self):
        for i in range(10):
            for s in range(100,500,100):
                fbs = [fillGradient((s,s), (1,0,0), (0,1,0)) for j in range(i)]

                for fb in fbs:
                    assert(fb.framebuffer.type.storageType == Float3)
                    assert(fb.framebuffer.size == (s,s))
        
if __name__ == "__main__":
    unittest.main()
