
from pyglew import *

from pygpu.utils.property import propget
from pygpu.GPU.gputypes import *

class Texture(object):
    @staticmethod
    def typeToOpenGL(type):
        if type == Float:
            return GL_R
        elif type == Float2:
            ## return GL_RG
            raise RuntimeError("Cannot have float2-textures!")
        elif type == Float3:
            return GL_RGB
        elif type == Float4:
            return GL_RGBA
        else:
            assert False
 

    def __init__(self, internalFormat, size, target,
                 dataFormat = GL_RGBA,
                 dataType = GL_UNSIGNED_BYTE,
                 data = None):
        self.target = target
        self.size = size
        self.texNo = glGenTextures(1)
        glBindTexture(target, self.texNo)

        w,h = size
        glTexImage2D(target, 0, internalFormat, w, h,
                     0, dataFormat, dataType, data)
        glBindTexture(target, 0)

    def __del__(self):
        if hasattr(self, 'texNo'):
            glDeleteTextures(1, [self.texNo])

    def bind(self, texUnit=0):
        glActiveTextureARB(GL_TEXTURE0_ARB + texUnit)
        glBindTexture(self.target, self.texNo)

    def draw(self):
        w,h = self.size

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glBegin(GL_QUADS)
        glTexCoord2f(-0.50, -0.50)
        glVertex2f(0, 0)

        glTexCoord2f(-0.50, h+0.50)
        glVertex2f(0, h)

        glTexCoord2f(w+0.50, h+0.50)
        glVertex2f(w, h)

        glTexCoord2f(w+0.50, -0.50)
        glVertex2f(w,0)
        glEnd()

#         glMatrixMode(GL_PROJECTION)
#         glPopMatrix()

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()




