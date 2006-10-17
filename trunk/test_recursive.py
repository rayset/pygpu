
from pygpu import *
from pygpu.types import *


def f(x=Int):
    return g(x)

def g(x):
    return x

import pygame
from pygame.locals import *
from pyglew import *

pygame.display.init()
surface = pygame.display.set_mode((512,512), OPENGL|DOUBLEBUF)

glewInit()

initPyGPU()

f = pygpu.compile(f)

