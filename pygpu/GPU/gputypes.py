
from copy import copy
from types import *
import pygpu.compiler.variable 
import pygpu.GPU.infer 
import pygpu.GPU.operations


class TypeBase(object):
    def __init__(self):
        self.castTargets = {}

    def addCastTarget(self, targetType, func):## -> None
        assert targetType not in self.castTargets
        self.castTargets[targetType] = func

    def castTo(self, targetType): ## -> Function or None
        return self.castTargets.get(targetType, None)

class BasicType(TypeBase):
    def __init__(self, name):
        TypeBase.__init__(self)
        self.shape = (1,)
        self.name = name
        
    def __len__(self):
        return 1

    def __str__(self): ## -> String
        return self.name


Float1 = Float = BasicType("float")
Int = BasicType("int")
Bool = BasicType("bool")
GPUNone = BasicType("none")

class VectorType(TypeBase):
    def __init__(self, baseType, shape):
        TypeBase.__init__(self)
        self.baseType = baseType
        self.shape = copy(shape)
        self.name = str(self)

    def __len__(self):
        return self.shape[0]

    def __str__(self):
        return "%s%s" % (self.baseType, self.shape[0])
                         ## "x".join(map(lambda x: str(x), self.shape)))

Float2 = VectorType(Float, (2,))
Float3 = VectorType(Float, (3,))
Float4 = VectorType(Float, (4,))

Int.addCastTarget(Float, id)
                  

Float.addCastTarget(Float2,
                    lambda x: pygpu.compiler.variable.Swizzle(Float2, x, [0,0]))
Float.addCastTarget(Float3,
                    lambda x: pygpu.compiler.variable.Swizzle(Float3, x, [0,0,0]))
Float.addCastTarget(Float4,
                    lambda x: pygpu.compiler.variable.Swizzle(Float4, x, [0,0,0,0]))



Position = Float2

Int2 = VectorType(Int, (2,))
Int3 = VectorType(Int, (3,))
Int4 = VectorType(Int, (4,))

Bool2 = VectorType(Bool, (2,))
Bool3 = VectorType(Bool, (3,))
Bool4 = VectorType(Bool, (4,))


class SamplerType(TypeBase):
    def __init__(self, storageType, accessType=Float2, filterMode=''):
        TypeBase.__init__(self)
        assert(storageType in [Float,Float2,Float3,Float4])

        self.storageType = storageType
        self.accessType = accessType
        self.filterMode = filterMode

        self.name = "samplerRECT" 

    def emit_call(self, block, tex, pt):
        tmp = pygpu.compiler.variable.TemporaryVariable(self.storageType)

        assert pygpu.GPU.infer.typeOf(pt) == self.accessType
        block.add(pygpu.GPU.operations.GPUSample(tmp, tex, pt, self.filterMode))
        return tmp
    
    def __str__(self):
        ## return "sampler%s" % (self.filterMode)
        return "<sampler %s %s %s %s>" % ("RECT",
                                          self.storageType,
                                          self.accessType,
                                          self.filterMode)

RGBAImage = SamplerType(Float4)
RGBImage = SamplerType(Float3)
RGImage = SamplerType(Float2)
RImage = SamplerType(Float)

class EmptyTexture:
    def __init__(self, type):
        self.type = type
        self.texNo = 0

GPUNone.addCastTarget(RGBImage,lambda x: EmptyTexture(RGBImage))

RImage.addCastTarget(RGBImage, lambda x: x)



def cast(x, targetT):
    t = pygpu.GPU.infer.typeOf(x)
    if targetT == t:
        return x
    else:
        f = t.castTo(targetT)
        if f:
            return f(x)
        else:
            raise TypeError("Cannot cast '%s' to %s." % (x,targetT))
