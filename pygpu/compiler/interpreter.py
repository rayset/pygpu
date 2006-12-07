
import sys, types, string, operator, traceback, dis
from opcode import *
from copy import copy

from pygpu.compiler.variable import *
from pygpu.compiler.block import Block
from pygpu.compiler.stack import Stack
import pygpu.GPU.functions
from pygpu.GPU.gputypes import *
from pygpu.GPU.infer import typeOf
from pygpu.GPU.utils import *
from pygpu.utils import *
from pygpu.GPU.operations import *
from pygpu.exceptions import PyGPUException

cmp_op = (GPULt, GPULe, GPUEq, GPUNe, GPUGt, GPUGe,
          GPUIn, GPUNotIn, GPUIs, GPUIsNot, GPUExceptionMatch, GPUBAD)

def mangle(name):
    return name.replace('+', '_')

class PyGPUInterpreter(object):
    def compile(self, func, args = None):
        co = func.func_code
        defaults = func.func_defaults
        self.func = func
        self.names = co.co_names
        self.code = co.co_code
        self.locals = [LocalVariable(co.co_varnames[i]) for i in range(co.co_nlocals)]

        #print "***", func.func_name, "***"
        #dis.dis(func)
        #print 
        
        block = Block(func.func_name)
        stack = Stack()

        argIndices = range(co.co_argcount)

        block.locals = self.locals[co.co_argcount:]

        
        if args is None:
            if not defaults:
                raise PyGPUException("Cannot compile function '%s'. Cannot find type-annotation!" % func.func_name)
            defaultOffset = co.co_argcount-len(defaults)

            for name, argI in zip(co.co_varnames,argIndices):
                l = argI-defaultOffset 
                if l >= 0:
                    t = defaults[l]
                else:
                    t = None
                var = ArgumentVariable(name, t)
                self.locals[argI] = var
                block.args.append(var)
                
        else:
            n = len(defaults)
            constArgs, varArgs = args[:-n], args[-n:]

            names = co.co_varnames[len(constArgs):-n-1]
            
            for arg, type in zip(args[-n:], defaults):
                print arg.type, type

            argI = 0
            for ca in constArgs:
                self.locals[argI] = ca
                argI += 1

                # mangle block name when we're generatively
                # evaluating a function
                block.name += "_%s" % (id(ca)) 

            ## Verify that the passed types are correct
            for arg, type in zip(varArgs, defaults):
                assert arg.type == type
                self.locals[argI] = arg
                argI += 1

            block.args = varArgs

            
        self.currentLocals = {}
        self.constants = co.co_consts
        

        #for local in self.locals:
        #try:
        # local.register(block)
        #except AttributeError:
        #    pass

        self.interpret(stack, block, 0)

        return block

    def interpret(self, stack, block, starti, endi = None):
        code = self.code
        
        i = starti
        if endi is None:
            endi = len(code)
        extended_arg = 0
        free = None

        while i < endi:
            c = self.code[i]
            op = ord(c)
            name = opname[op]
            
            i = i+1
            if op >= HAVE_ARGUMENT:
                oparg = ord(code[i]) + ord(code[i+1])*256 + extended_arg
                i = i+2
            else:
                oparg = None
                
            self.index = i

            name = mangle(name)

            if hasattr(self, name):
                i2 = getattr(self, name)(stack, block, oparg)
            else:
                print "Unknown op-code: %s" % name
                sys.exit(1)
                
            if i2 is not None:
                i = i2

        return i

    def lookup(self, v):
        try:
            return self.currentLocals.get(v,v)
        except TypeError:
            return v

    def remove(self, v):
        try:
            del self.currentLocals[v] 
        except KeyError:
            pass

        
    def LOAD_CONST(self, stack, block, oparg):
        stack.push(Constant(self.constants[oparg]))

    def LOAD_FAST(self, stack, block, oparg):
        stack.push(self.locals[oparg])

    def LOAD_ATTR(self, stack, block, oparg):
        stack.push(getattr(stack.pop(), self.names[oparg]))

    def LOAD_GLOBAL(self, stack, block, oparg):
        name = self.names[oparg]
        if name in pygpu.GPU.functions.__dict__:
            stack.push(getattr(pygpu.GPU.functions, name))
        else:
            stack.push(eval(name, self.func.func_globals))

    def STORE_FAST(self, stack, block, oparg):

        v = self.lookup(stack.pop())
        t = self.locals[oparg]
        if t.type == None:
            try:
                t.type = typeOf(v)
            except TypeError:
                pass
        else:
            assert t.type == typeOf(v)

        if t.type is not None:
            block.add(GPUMov(t,v))
            

        #if isConstant(v) :
        if not isinstance(v, TemporaryVariable):
            self.currentLocals[t] = v
        #else:
        #    self.remove(t)
            
    def SETUP_LOOP(self, stack, block, oparg):
        pass

    def CALL_FUNCTION(self, stack, block, oparg):
        args = stack.popN(oparg&0xff)
        kwordArgs = stack.popN((oparg>>8) & 0xff)
        assert kwordArgs is None
        f = stack.pop()
        args = map(self.lookup, args)

        if isConstant(args):
            args = stripConstant(args)
            try:
                if hasattr(f, "call"):
                    result = f.call(*args)
                else:
                    result = f(*args)
            except Exception, e:
                print "When trying to call %s: %s" % (f, e)
                sys.exit(1)

        else:
            try:
                result = f.emit_call(block, *args)
            except AttributeError:
                interp = PyGPUInterpreter()
                funcBlock = interp.compile(f, args)
                block.addFunction(funcBlock)


                ## !!FIXME!! implement multiple return functions (can be mapped
                ## via out-variables)
                result = TemporaryVariable(funcBlock.returnType)
                block.add(GPUCall(result, funcBlock.name, funcBlock.args))

        stack.push(result)

    def GET_ITER(self, stack, block, oparg):
        stack.push(iter(self.lookup(stack.pop())))

    def FOR_ITER(self, stack, block, oparg):
        it = stack.pop()

        ## unpack the next STORE_FAST instruction
        i = self.index
        c1 = ord(self.code[i])
        if opname[c1] == "STORE_FAST":
            ## only one loop variable
            oparg1 = ord(self.code[i+1]) + ord(self.code[i+2])*256
            iterVars = [self.locals[oparg1]]
            
        elif opname[c1] == "UNPACK_SEQUENCE":
            ## multiple loop variables
            noLoopVars = ord(self.code[i+1]) + ord(self.code[i+2])*256
            iterVars = noLoopVars*[None]
            for j in range(noLoopVars):
                i2 = i+3*(j+1)
                c1 = ord(self.code[i2])
                oparg1 = ord(self.code[i2+1]) + ord(self.code[i2+2])*256
                assert opname[c1] == "STORE_FAST"
                iterVars[j] = self.locals[oparg1]
            
        if isDummyIterator(it):
            if len(iterVars) != 1:
                raise NotImplementError()
            iterVar = iterVars[0]
            if iterVar.type is None:
                iterVar.type = it.type

            currentLocals2 = self.currentLocals
            self.currentLocals = {}
                
            self.currentLocals[oparg1] = iterVar 
            stack.push(iterVar)
            block.add(GPUBeginLoop(iterVar, it))
            self.interpret(stack, block, i+3, i+3+oparg)
            block.add(GPUEndLoop())

            # remove any variable that was assigned to inside
            # the loop block from the currently known variables.
            for k in self.currentLocals.iterkeys():
                if k in currentLocals2:
                    del currentLocals2[k]

            self.currentLocals = currentLocals2
            block.add(GPUSub(iterVar, it.stop, it.step))
            try:
                del self.currentLocals[iterVar] 
            except KeyError:
                pass
                
        else:
            if len(iterVars) > 1:
                startI = self.index + 3*(len(iterVars) + 1)
                endI = self.index + oparg
                for x in it:
                    for iterVar,v in zip(iterVars, x):
                        self.currentLocals[iterVar] = v
                    self.interpret(stack, block, startI, endI)
            else:
                startI = self.index + 3
                endI = self.index + oparg
                iterVar = iterVars[0]
                for x in it:
                    self.currentLocals[iterVar] = x
                    self.interpret(stack, block, startI, endI)
                
        return i+oparg 

    def RETURN_VALUE(self, stack, block, oparg):
        v = self.lookup(stack.pop())
        block.returnType = v.type
        block.add(GPURet(v))

    def INPLACE_ADD(self, stack, block, oparg):
        l,r = stack.popN(2)
        if l in self.currentLocals and isConstant(r):
            stack.push(self.currentLocals[l]+r)
        else:
            block.add(GPUAdd(l,self.lookup(l),self.lookup(r)))
            stack.push(l)
            self.remove(l)

    def INPLACE_SUBTRACT(self, stack, block, oparg):
        l,r = stack.popN(2)
        if l in self.currentLocals and isConstant(r):
            stack.push(self.currentLocals[l]-r)
        else:
            block.add(GPUSub(l,self.lookup(l),self.lookup(r)))
            stack.push(l)
            self.remove(l)

    def BINARY_ADD(self, stack, block, oparg):
        l,r = stack.popN(2)
        if isConstant(l) and isConstant(r):
            stack.push(l+r)
        elif l in self.currentLocals and isConstant(r):
            #print repr(l),repr(r)
            #print self.currentLo
            stack.push(self.currentLocals[l]+r)
        else:
            tmp = TemporaryVariable(typeOf(l))
            block.add(GPUAdd(tmp,self.lookup(l),self.lookup(r)))
            stack.push(tmp)

    def BINARY_SUBTRACT(self, stack, block, oparg):
        l,r = stack.popN(2)
        if isConstant(l) and isConstant(r):
            stack.push(l-r)
        elif l in self.currentLocals and isConstant(r):
            stack.push(self.currentLocals[l]-r)
        else:
            tmp = TemporaryVariable(typeOf(l))
            block.add(GPUSub(tmp,self.lookup(l),self.lookup(r)))
            stack.push(tmp)

    def BINARY_MULTIPLY(self, stack, block, oparg):
        l,r = stack.popN(2)

        if l in self.currentLocals and isConstant(r):
            stack.push(pygpu.GPU.functions.mul.call(self.currentLocals[l],r))
        else:
            l,r = map(self.lookup, (l,r))
            stack.push(pygpu.GPU.functions.mul.emit_call(block, l, r))

    def BINARY_DIVIDE(self, stack, block, oparg):
        l,r = stack.popN(2)
        l,r = map(self.lookup, (l,r))
        stack.push(pygpu.GPU.functions.div.emit_call(block, l, r))

    def BINARY_POWER(self, stack, block, oparg):
        l,r = stack.popN(2)
        l,r = map(self.lookup, (l,r))
        stack.push(pygpu.GPU.functions.pow.emit_call(block, l, r))

    def JUMP_ABSOLUTE(self, stack, block, oparg):
        pass

    def POP_BLOCK(self, stack, block, oparg):
        pass

    def COMPARE_OP(self, stack, block, oparg):
        op = cmp_op[oparg]
        l,r = stack.popN(2)
        tmp, gpuOp = op(l,r)
        block.add(gpuOp)
        stack.push(tmp) 

    def JUMP_IF_FALSE(self, stack, block, oparg):
        i = self.index
        
        cond = stack.top()
        trgt = i+oparg
            
        currentLocals2 = self.currentLocals
        stack2 = stack

        self.currentLocals = copy(currentLocals2)
        stack = copy(stack2)
        block.add(GPUIf(cond))
        join = self.interpret(stack, block, i, trgt)
        block.add(GPUElse())
        self.currentLocals = copy(currentLocals2)
        stack = copy(stack2)
        i = self.interpret(stack, block, trgt, join)
        block.add(GPUEndIf())
        self.currentLocals = currentLocals2
        stack = stack2

        return i

    def POP_TOP(self, stack, block, oparg):
        stack.pop()

    def JUMP_FORWARD(self, stack, block, oparg):
        return self.index + oparg

    def PRINT_ITEM(self, stack, block, oparg):
        print stack.pop(),

    def PRINT_NEWLINE(self, stack, block, oparg):
        print

    def UNARY_NEGATIVE(self, stack, block, oparg):
        v = stack.pop()
        if isConstant(v):
            stack.push(-v)
        else:
            tmp = TemporaryVariable(v.type)
            block.add(GPUUNeg(tmp, v))
            stack.push(tmp)

    def BUILD_LIST(self, stack, block, oparg):
        if oparg == 0:
            stack.push([])
        else:
            elts = stack.popN(oparg)
            stack.push(list(elts))
        
    def LIST_APPEND(self, stack, block, oparg):
        l,v = map(self.lookup, stack.popN(2))
        l.append(v)
        #print l
        ## stack.push(l)

    def DELETE_FAST(self, stack, block, oparg):
        self.locals[oparg] = None
        
    def DUP_TOP(self, stack, block, oparg):
        stack.push(stack.top())

    def UNPACK_SEQUENCE(self, stack, block, oparg):
        elts = stack.pop()
        assert len(elts) == oparg
        for arg in reversed(elts):
            stack.push(arg)

    def BINARY_SUBSCR(self, stack, block, oparg):
        index = stripConstant(stack.pop())
        v = stack.pop()
        stack.push(v[index])


    def SLICE_3(self, stack, block, oparg):
        end = stack.pop()
        start = stack.pop()
        lst = stack.pop()

        start = stripConstant(start)
        end = stripConstant(end)

        stack.push(lst[start:end])

    def BUILD_TUPLE(self, stack, block, oparg):
        elts = stack.popN(oparg)
        stack.push(tuple(elts))

        
if __name__ == '__main__':
    interpret(0)
    #block.pp()

    from cg_backend import CgBackend

    f = file("trivial.cg", "w")
    backend = CgBackend(f)
    backend.emit(block)
    f.close()
    
    for line in file("trivial.cg", "r"):
        print line,

    import os
    os.system("cgc -profile fp40 trivial.cg")
