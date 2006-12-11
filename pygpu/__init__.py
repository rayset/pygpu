
__name__ = 'pygpu'
__author__ = 'Calle Lejdfors <calle.lejdfors@cs.lth.se>'

## This is the documantation for the top-level module of PyGPU
#
# Here there is some more information
#
# @author Calle Lejdfors <calle.lejdfors@cs.lth.se>
#
#

__all__ = ['initPyGPU',
           'gpu',
           'loadImage',
           'imageFromArray'           
           ]

import copy 

from pygpu.compiler import PyGPUInterpreter
from pygpu.GPU.image import *
from pygpu.GPU.framebuffer import FramebufferFactory
import pygpu.backends

from pyglew import *


## Initialization function for PyGPU
#
#
def initPyGPU(backend=None):
    ## !!FIXME!! More goo goes here!
    ## pygpu.GPU.selectFramebuffer()
    if not GLEW_EXT_framebuffer_object():
        raise RuntimeError("Your card/driver does not support framebuffers!\n" +
                           "Upgrading your drivers might solve this problem.")
             
    if not GLEW_ARB_multitexture():
        raise RuntimeError("Your card/driver does not support multitexturing!\n" +
                           "Upgrading your drivers might solve this problem.")

    pygpu.backends.chooseBackend(backend)

def _default_size(*args):
    for arg in args:
        if hasattr(arg, 'size'):
            return arg.size

    raise RuntimeError("Could not infer size!")

class GPUFunction(object):
    def __init__(self, func, size = _default_size):
        self.func = func
        self.size = size

    def __call__(self, *args):
        # !!FIXME!! this must be implemented!
        inputType = self.func.varyingType
        returnType = self.func.returnType

        size = self.size(*args)

        tex = FramebufferFactory.create(returnType, size)

        tex.BeginCapture()
        self.func.bind(*args)
        tex.draw()
        self.func.release()
        tex.EndCapture()
        
        return tex
       
    

class GPUFunctionHelper(object):
    def __init__(self, **kwords):
        self.kwords = kwords

    def __call__(self, *args, **kwords):
        kwords2 = copy.copy(self.kwords)
        kwords2.update(kwords)
        return gpu(*args, **kwords2)


def gpu(*args, **kwords):
    if args:
        assert len(args) == 1
        f = args[0]

        interpreter = PyGPUInterpreter()
        block = interpreter.compile(f)
        gpuFunc = pygpu.backends.backend.emit(block)
        return GPUFunction(gpuFunc, **kwords)
    else:
        return GPUFunctionHelper(**kwords)
    
        







