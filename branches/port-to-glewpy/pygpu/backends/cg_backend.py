
__all__ = ['CgBackend']

import sys, os

from Cg import *

import pygpu.GPU.gputypes
import pygpu.compiler.variable ## isConstant, isSwizzle
from pygpu.GPU.infer import *


class CgBackend(object):
    context = None
    profile = None
    cacheDirectory = '.cg_cache'
    
    def __init__(self):
        CgBackend.context = cgCreateContext()
        CgBackend.profile = CG_PROFILE_ARBFP1 ##cgGLGetLatestProfile(CG_GL_FRAGMENT) 

        ## allow Cg to manage our texture state
        cgGLSetManageTextureParameters(CgBackend.context, True)
        
        
    def emit(self, block):
        name = block.name

        if not os.access(CgBackend.cacheDirectory, os.F_OK):
            os.mkdir(CgBackend.cacheDirectory)

        path = os.path.join(CgBackend.cacheDirectory, "%s.cg" % name)

        #        try:
        CgCodeGen(file(path, 'w+')).emit(block)
        #        except Exception, e:
        #            print "Cg code generation failed with: %s" % e
        #            sys.exit(1)

        return CgFunctionWrapper(path,
                                 name,
                                 block.returnType,
                                 block.args)
        

def cgGetErrors():
    yield cgGetError()
    
class CgFunctionWrapper(object):
    def __init__(self, path, topEntry, returnType, argList):
        self.program = cgCreateProgramFromFile(CgBackend.context,
                                               CG_SOURCE,
                                               path,
                                               CgBackend.profile,
                                               topEntry,
                                               None)
        if not self.program:
            raise RuntimeError("Cg runtime error while compiling program:\n" + \
                               cgGetLastListing(CgBackend.context))
                               ##"\n".join([cgGetErrorString(error) for error in cgGetErrors()]))

        cgGLLoadProgram(self.program)

        cgArgs = []
        param = cgGetFirstParameter(self.program, CG_PROGRAM)
        while param != None:
            if cgGetParameterVariability(param) != CG_CONSTANT:
                cgArgs.append(param)
            param = cgGetNextParameter(param)

        ## !!FIXME!! remove assumption that only 2D images are admissible
        ## assert argList[-1].type == pygpu.GPU.gputypes.Float2

        self.args = zip(argList, cgArgs)[0:-1]
        self.varyingType = argList[-1].type
        self.returnType = returnType
        

    def bind(self, *args):
        assert len(args) == len(self.args)
        for arg, (pygpuArg, cgParam) in zip(args, self.args):
            arg = cast(arg, pygpuArg.type)
            ## arg.bind(self, cgParam)
            typeName = cgGetTypeString(cgGetParameterType(cgParam))
            getattr(self, "bind_" + typeName)(cgParam, arg)
            
        cgGLBindProgram(self.program)
        cgGLEnableProfile(CgBackend.profile)

    def release(self):
        cgGLDisableProfile(CgBackend.profile)
        
    def bind_samplerRECT(self, cgParam, im):
        cgGLSetTextureParameter(cgParam, im.texNo)

    def bind_int(self, cgParam, i):
        cgGLSetParameter1f(cgParam, i)

    def bind_float(self, cgParam, i):
        cgGLSetParameter1f(cgParam, i)

    def bind_float2(self, cgParam, (x,y)):
        cgGLSetParameter2f(cgParam, x, y)

    def bind_float3(self, cgParam, (x,y,z)):
        cgGLSetParameter3f(cgParam, x, y, z)

    def _getSource(self):
        return cgGetProgramString(self.program, CG_PROGRAM_SOURCE)
        
        

class CgCodeGen(object):
    def __init__(self, output):
        self.indentation = 0
        self.output = output

        self.declared = []
        self.preprocessArgs = []

    def push_indent(self):
        self.indentation += 3

    def pop_indent(self):
        self.indentation -= 3

    def write(self, str, terminator = ";\n"):
        print >> self.output, " "*self.indentation + "%s" % str,
        if terminator is False:
            print >> self.output
        else:
            print >> self.output, terminator,

    def writeln(self, str):
        self.write(str)

    def declareArgs(self, args):
        uniform = map(lambda arg: "uniform " + self.toCgArg(arg), args[:-1])
        varying = map(lambda arg: "varying " + self.toCgArg(arg) + ":TEXCOORD", args[-1:])

        self.write(",\n".join(uniform+varying), False)
        

    def declare(self, v):
        if v not in self.declared:
            self.writeln("%s %s" % (v.type, v))
            self.declared.append(v)

    def emit(self, block):
        self.emitFunction(block, "COLOR")

    def emitFunction(self, block, semantic = None):
        ## Recursively compile all callees
        for func in block.functions:
            CgCodeGen(self.output).emitFunction(func)
        
        self.write(self.toCg(block.returnType), False)
        self.write("%s(" % block.name, False)
        self.push_indent()
        #if semantic is not None:
        self.declareArgs(block.args)
        #else:
        #map(lambda arg: "uniform " + self.toCgArg(arg), args[:-1])
        #    print map(str,block.args)
        #    sys.exit(1)
        self.pop_indent()
        if semantic is not None:
            self.write(") : %s" % semantic, False)
        else:
            self.write(")", False)
            
        self.write("{", False)
        self.push_indent()

        for p in self.preprocessArgs:
            p()
        
        for v in block.locals:
            if v.type is not None:
                self.declare(v)
        for instr in block.instructions:
            instr.emit(self)
        self.pop_indent()
        self.write("}", False)

    def toCgArg(self, x):
        t = typeOf(x)
        self.declared.append(x)
        return getattr(self, "cg_arg_" + t.name)(x)

    def toCg(self, x):
        if pygpu.compiler.variable.isConstant(x):
            t = typeOf(x)
            # print t
            # sys.exit(0)
            try:
                return getattr(self, "cg_" + t.name)(x)
            except NameError:
                raise TypeError("Cannot convert PyGPU type '%s' to a Cg type" % (t,))

        elif pygpu.compiler.variable.isSwizzle(x):
            _swizzles = ['x', 'y', 'z', 'w']
            swizzle = [_swizzles[i] for i in x.swizzle]

            return "(%s).%s" % (self.toCg(x.var),
                                "".join(swizzle))
            
        else:
            return str(x)

    def cg_arg_samplerRECT(self, x):
        return "samplerRECT %s" % (x,)

    def cg_arg_int(self, x):
        self.preprocessArgs.append(lambda : self.Call(x, "round", [x]))
        return "float %s" % (x,)

    def cg_arg_int2(self, x):
        shadow = "%s_f" % (x,)
        self.preprocessArgs.append(lambda : self.writeln("int2 %s = round(%s_f);" % (x,x)))
        return "float2 %s" % (shadow,)

    def cg_arg_int3(self, x):
        self.preprocessArgs.append(lambda : self.Call(x, "round", [x]))
        return "float3 %s" % (x,)

    def cg_arg_int4(self, x):
        self.preprocessArgs.append(lambda : self.Call(x, "round", [x]))
        return "float4 %s" % (x,)

    def cg_arg_float(self, x):
        return "float %s" % (x,)

    def cg_arg_float2(self, x):
        return "float2 %s" % (x,)

    def cg_arg_float3(self, x):
        return "float3 %s" % (x,)

    def cg_arg_float4(self, x):
        return "float4 %s" % (x,)

    def cg_int(self, x):
        return "int(%s)" % (x)

    def cg_float(self, x):
        return "float(%s)" % (x)

    def cg_float2(self, x):
        return "float2(%s, %s)" % (x[0], x[1])

    def cg_float3(self, x):
        return "float3(%s, %s, %s)" % (x[0], x[1], x[2])

    def cg_float4(self, x):
        return "float4(%s, %s, %s, %s)" % (x[0], x[1], x[2], x[3])

    def Mov(self, t, s):
        s = self.toCg(s)
        self.declare(t)
        self.write("%s = %s" % (t,s))

    def Add(self, t, l, r):
        l,r = map(self.toCg, (l,r))
        self.declare(t)
        self.write("%s = %s + %s" % (t,l,r))

    def Sub(self, t, l, r):
        l,r = map(self.toCg, (l,r))
        self.declare(t)
        self.write("%s = %s - %s" % (t,l,r))

    def Mul(self, t, l, r):
        l,r = map(self.toCg, (l,r))
        self.declare(t)
        self.write("%s = %s * %s" % (t,l,r))

    def Div(self, t, l, r):
        l,r = map(self.toCg, (l,r))
        self.declare(t)
        self.write("%s = %s / %s" % (t,l,r))

    def Pow(self, t, l, r):
        l,r = map(self.toCg, (l,r))
        self.declare(t)
        self.write("%s = pow(%s, %s)" % (t,l,r))

    def Ret(self, x):
        x = self.toCg(x)
        self.write("return %s" % (x))

    def Lt(self, tmp, l, r):
        self.declare(tmp)
        self.write("%s = %s < %s" % (tmp,l,r))

    def If(self, cond):
        self.write("if ( %s ) {" % (cond,), False)
        self.push_indent()

    def Else(self):
        self.pop_indent()
        self.write("} else {", False)
        self.push_indent()

    def EndIf(self):
        self.pop_indent()
        self.write("}", False)

    def BeginLoop(self, v, it):
        self.write("for(%s = %s ; %s < %s ; %s += %s) {" % (v, it.start, v, it.stop, v, it.step), False)
        self.push_indent()

    def EndLoop(self):
        self.pop_indent()
        self.write("}", False)

    def Sample(self, tmp, tex, pt, filterMode):
        self.declare(tmp)
        self.write("%s = tex%s%s(%s, %s).%s" % (tmp, "RECT", filterMode, tex, pt,
                                                "xyzw"[0:len(tmp.type)]))

    def Call(self, result, funcName, args):
        self.declare(result)
        self.writeln("%s = %s(%s)" % (result, funcName, ", ".join(map(self.toCg,args))))
