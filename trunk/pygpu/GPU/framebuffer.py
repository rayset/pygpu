
from pygpu.GPU.nvidia_framebuffer import NVIDIAFramebuffer
from pygpu.GPU.ati_framebuffer import ATIFramebuffer
from pygpu.compiler.stack import Stack

print "Selecting framebuffer implementation...",
 
if NVIDIAFramebuffer.isSupported():
    print "using NVIDIA!"
    Framebuffer = NVIDIAFramebuffer

elif ATIFramebuffer.isSupported():
    print "using ATI!"
    Framebuffer = ATIFramebuffer

else:
    raise RuntimeError("Cannot find a supported framebuffer implementation!")


class FramebufferWrapper:
    def __init__(self, framebuffer, cacheStack):
        self.framebuffer = framebuffer
        self.cacheStack = cacheStack

        self.size = framebuffer.size
        self.type = framebuffer.type
        self.texNo = framebuffer.texNo
        
    def __del__(self):
        self.cacheStack.push(self)

    def __str__(self):
        return "cached(%s)" % self.framebuffer

    def BeginCapture(self):
        self.framebuffer.BeginCapture()

    def draw(self):
        self.framebuffer.draw()

    def EndCapture(self):
        self.framebuffer.EndCapture()

    def show(self):
        self.framebuffer.show()


class FramebufferFactory:
    cache = {}

    @staticmethod
    def create(type, size):
        sizeCache = FramebufferFactory.cache.setdefault(type, {})
        available = sizeCache.setdefault(size, Stack())

        if available:
            return available.pop()
        else:
            return FramebufferWrapper(Framebuffer(type, size), available)


            
