"""
@mainpage PyGPU - Python for the GPU

Haven't you ever dreamt of writing code in a very high level
language and have that code execute at speeds rivaling that of
lower-level languages? PyGPU (http://www.cs.lth.se/~calle/pygpu) is
a compiler that lets you write image processing programs in Python
that execute on the graphics processing
unit (%GPU) present in modern graphics cards. This enables image
processing algorithms to take advantage of the performance of the
%GPU. In some applications, performance increases approach an order of
magnitude, compared to CPUs. 

Existing methods for programming the %GPU uses either specialised
languages (such as Cg, HLSL, or GLSL) or an embedded language in C++
(Sh) or C# (Accelerator). The specialised languages are generally very
low-level (on the level of C with some simple C++
constructs). Furthermore, they require intimate knowledge
of advanced graphics programming concepts, as well as quite
a bit of glue-code to handle parameter passing and render
pipeline setup. 

The embedded approaches admit a higher level of abstraction (being
embedded in somewhat higher level languages) and also does away with
a lot of the glue code necessary with using specialised
languages. However, neither C++ or C# come close to the simple,
direct flexibility and expressive power of more dynamic languages
such as Python or Ruby. 

PyGPU is an embedded language in Python, that allow most of Python
features (list-comprehensions, higher-order functions, iterators) to
be used for constructing %GPU algorithms. It uses a image abstraction
to abstract away implementation details of the %GPU, while still
allowing translation to very efficient %GPU native-code.  

@author Calle Lejdfors <calle.lejdfors@cs.lth.se>
"""

"""
@package pygpu 
 
This is the top-level module in PyGPU
"""

__name__ = 'pygpu'
__author__ = 'Calle Lejdfors <calle.lejdfors@cs.lth.se>'
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
# This function initializes PyGPU. It must be called after an OpenGL
# context has been created.
#
# @arg \a backend Manually override which backend to use.
# @bug Passing a \a backend is currently is not implemented. The
# backend is inferred when the module is imported instead. As a
# consequence PyGPu must be imported \e after an OpenGL context has
# been created.
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

## Function decorator for PyGPU functions
#
# This decorator marks a function as being a PyGPU function that
# should execute on the %GPU. 
#
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
    
        







