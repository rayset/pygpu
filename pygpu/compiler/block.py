import string

class Block(object):
    def __init__(self, name):
        self.name = name
        self.instructions = []

        self.args = []
        self.locals = []

        self.returnType = None

        self.functions = []
        
    def __getitem__(self,i):
        return self.instructions[i]

    def __len__(self):
        return len(self.instructions)
    
    def pp(self):
        print string.join([str(i) for i in self.instructions], "\n")

    def add(self, instr):
        self.instructions.append(instr)

    def insert(self, index, instr):
        if self.instructions == []:
            self.instructions.append(instr)
        else:
            self.instructions.insert(index, instr)

    def remove(self, index):
	del self.instructions[index]

    def addArgument(self, arg):
        self.args.append(arg)

    def addLocal(self, arg):
        self.locals.append(arg)

    def addFunction(self, funcBlock):
        self.functions.append(funcBlock)
