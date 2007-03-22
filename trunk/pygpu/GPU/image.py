
import numpy

import pygame
from pyglew import *

from pygpu.utils.property import propget
from pygpu.GPU.framebuffer import Framebuffer
from pygpu.GPU.gputypes import RGBImage, RGBAImage

class ImageBase(object):
    def __init__(self):
        self._texNo = None

    @propget
    def texNo(self):
        if self._texNo is None:
            self._texNo = glGenTextures(1)
            glBindTexture(self.target, self._texNo)

            w,h = self.size

            dataType = self.dataType
            data = self.data

            assert self.target == Framebuffer.TextureTarget
            glTexImage2D(self.target, 0, self.internalFormat, w, h,
                         0, self.format, self.dataType, data)

        return self._texNo

    def bind(self, factory, *args):
        ##glActiveTextureARB(GL_TEXTURE0_ARB + texUnit)
        ##glBindTexture(self.target, self.texNo)
        factory.bindSamplerRECT(self.texNo, *args)

    def update(self):
        self.bind(0)
        glCopyTexSubImage2D(self.target, 0, 0, 0, 0, 0, 512, 512)

    def display(self, ll = None, ur = None):
        if self.target == Framebuffer.TextureTarget:
            w,h = pygpu.gpufunc.GPUFunc.size 
        else:
            w,h = 1,1

        if ll:
            x,y = ll
        else:
            x,y = 0,0

        if ur:
            sw,sh = ur[0]-x,ur[1]-y
        else:
            sw,sh = self.size 

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0,w,0,h,0,1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
       
        glEnable(GL_SCISSOR_TEST)
        glScissor(x,y,sw,sh)

        fudge = +(0.5 - 0.1/w)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex3f(0.5, 0, 0)
        
        glTexCoord2f(w, 0)
        glVertex3f(w+fudge, 0, 0)
        
        glTexCoord2f(w, h)
        glVertex3f(w+fudge, h, 0)
        
        glTexCoord2f(0, h)
        glVertex3f(0.5, h, 0)
        glEnd();
        
        glDisable(GL_SCISSOR_TEST)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()


    
    def initRECTshow():
        ImageBase._ctx = cgCreateContext()
        ImageBase._showRECTprog = cgCreateProgram(ImageBase._ctx,
                                                  CG_SOURCE,
                                                  ImageBase._showRECT,
                                                  CG_PROFILE_ARBFP1,
                                                  "main",
                                                  None)
        assert(ImageBase._showRECTprog)
        cgGLLoadProgram(ImageBase._showRECTprog)
    initRECTshow = staticmethod(initRECTshow)

    def show(self, ll=None, ur=None):
        if self.target == Framebuffer.TextureTarget:
            if ImageBase._ctx == None:
                ImageBase.initRECTshow()
            cgGLBindProgram(ImageBase._showRECTprog)
            cgGLEnableProfile(CG_PROFILE_ARBFP1)
        else:
            glEnable(self.target)

        self.bind(0)
        self.display(ll, ur)

        if self.target == Framebuffer.TextureTarget:
            cgGLDisableProfile(CG_PROFILE_ARBFP1)
        else:
            glDisable(self.target)



class Image(ImageBase):
    def __init__(self, type, data, format, size,
                 dataType = GL_UNSIGNED_BYTE,
                 target = Framebuffer.TextureTarget):
        ImageBase.__init__(self)
        
        self.type = type

        self.data = data
        self.size = size
        self.format = format
        self.internalFormat = Framebuffer.typeToOpenGL(type.storageType, 32)
        self.dataType = dataType
        self.target = target

    def __str__(self):
        return "<Image %s %s size=%dx%d tex=%s>" % ("RECT", 32, self.size[0], self.size[1], self.texNo)




def loadImage(path, imageType):
    surface = pygame.image.load(path)

    bytesize = surface.get_bytesize()

    if bytesize == 3:
        format = GL_RGB
        mode = "RGB"
    elif bytesize == 4:
        format = GL_RGBA
        mode = "RGBA"
    else:
        raise ValueError("Unknown image mode!")

    data = pygame.image.tostring(surface, mode, True)

    return Image(imageType, data, format, surface.get_size())


def imageFromArray(array):
    assert len(numpy.shape(array)) == 3
    w,h,nColors = numpy.shape(array)

    if nColors == 3:
        type = RGBImage
        format = GL_RGB
    elif nColors == 4:
        type = RGBAImage
        format = GL_RGBA
    else:
        raise ValueError("Could not deduce number of color channels in the array!")
    
    dtype = array.dtype
    if dtype == numpy.uint8:
        dataType = GL_UNSIGNED_BYTE
    elif dtype == numpy.int8:
        dataType = GL_BYTE
    elif dtype == numpy.int32:
        dataType = GL_INT
    elif dtype == numpy.float32:
        dataType = GL_FLOAT
    else:
        raise ValueError("Unknown datatype in array!")

    #data = array.ravel().tostring()
    #return Image(type, data, format, (w,h), dataType)
    return Image(type, array, format, (w,h), dataType)
