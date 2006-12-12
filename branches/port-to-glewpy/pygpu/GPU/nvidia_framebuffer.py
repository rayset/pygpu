
import numpy

from glew import *
from Cg import *

from pygpu.backends.cg_backend import CgBackend
from pygpu.GPU.texture import Texture
from pygpu.GPU.gputypes import *
import pygpu.GPU.framebuffer 

class NVIDIAFramebuffer(Texture):
    _showRECTprogram = None

    TextureTarget = GL_TEXTURE_RECTANGLE_ARB

    @staticmethod
    def isSupported():
        return GLEW_ARB_texture_rectangle() and \
               GLEW_NV_float_buffer() 

    @staticmethod
    def typeToOpenGL(type, colorDepth):
        if colorDepth == 8:
            return Texture.typeToOpenGL(type)

        elif colorDepth == 32:
            if type == Float:
                return GL_FLOAT_R32_NV
            elif type == Float2:
                return GL_FLOAT_RG32_NV
            elif type == Float3:
                return GL_FLOAT_RGB32_NV
            elif type == Float4:
                return GL_FLOAT_RGBA32_NV
            else:
                assert False

        else:
            assert False
                

    def __init__(self, type, size, colorDepth = 32):
        if type == Float:
            self.type = RImage
        elif type == Float2:
            self.type = RGImage
        elif type == Float3:
            self.type = RGBImage
        elif type == Float4:
            self.type = RGBAImage
        else:
            raise RuntimeError("bork!")
            
     
        internalFormat = NVIDIAFramebuffer.typeToOpenGL(type, colorDepth)
        Texture.__init__(self, internalFormat, size, NVIDIAFramebuffer.TextureTarget)
        self.bind()
            
        w,h = size
        self.frameBuffer = glGenFramebuffersEXT(1)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frameBuffer);
        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,
                                  GL_COLOR_ATTACHMENT0_EXT,
                                  self.target, self.texNo, 0);

        ## depth buffer
        self.depthBuffer = glGenRenderbuffersEXT(1);
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, self.depthBuffer);
        glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT,
                                 GL_DEPTH_COMPONENT24, w, h);
        glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,
                                     GL_DEPTH_ATTACHMENT_EXT,
                                     GL_RENDERBUFFER_EXT, self.depthBuffer);
  
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0);
        
    def __del__(self):
        if hasattr(self, 'depthBuffer'):
            glDeleteRenderbuffersEXT(1, [self.depthBuffer])
        if hasattr(self, 'frameBuffer'):
            glDeleteFramebuffersEXT(1, [self.frameBuffer])
        Texture.__del__(self)

    def __str__(self):
        return "<NVIDIAFramebuffer %s %s %dx%d@%d fb=%d, tex=%d>" % \
               ("RECT", self.type, self.size[0], self.size[1],
                32, self.frameBuffer, self.texNo)

    def __array__(self):
        return self.toarray()

    def toarray(self):
        type = self.type.storageType 
        w,h = size = self.size
        
        if type == Float:
            glType = GL_RED
        elif type == Float2:
            ## glType = GL_LUMINANCE_ALPHA ## !!CHECKME!! is this correct???
            raise TypeError("Cannot create an array from a float2 texture!")
        elif type == Float3:
            glType = GL_RGB
        elif type == Float4:
            glType = GL_RGBA
        else:
            raise RuntimeError("Type %s cannot be used here!" % type)

        tex = pygpu.GPU.framebuffer.FramebufferFactory.create(type, size)
        tex.BeginCapture()
        self.show()
        data = glReadPixels(0, 0, w, h, glType, GL_FLOAT)
        tex.EndCapture()

        array = numpy.fromstring(data, dtype=numpy.float32)
        array.shape = (w,h,len(type))
        
        return array
        
    def BeginCapture(self):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frameBuffer);

    def EndCapture(self):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0);
        


    @staticmethod
    def initRECTshow():
        NVIDIAFramebuffer._showRECTprogram = cgCreateProgram(CgBackend.context,
                                                             CG_SOURCE,
                                                             """float4 main(in float2 tc:TEXCOORD,
                                                             uniform samplerRECT tex:TEXUNIT0) : COLOR
                                                             { return texRECT(tex, tc); }""",
                                                             CG_PROFILE_ARBFP1,
                                                             "main",
                                                             None)
        assert(NVIDIAFramebuffer._showRECTprogram)
        cgGLLoadProgram(NVIDIAFramebuffer._showRECTprogram)

    def show(self):
        if not NVIDIAFramebuffer._showRECTprogram:
            NVIDIAFramebuffer.initRECTshow()
        cgGLBindProgram(NVIDIAFramebuffer._showRECTprogram)
        cgGLEnableProfile(CG_PROFILE_ARBFP1)

        self.bind(0)
        self.draw()

        cgGLDisableProfile(CG_PROFILE_ARBFP1)
