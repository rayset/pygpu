
from copy import copy

class Stack(object):
    def __init__(self):
        self.repr = []

    def __str__(self):
        return "Stack%s" % map(str,self.repr)
    
    def __iter__(self):
	return iter(self.repr)

    def __len__(self):
        return len(self.repr)

    def size(self):
	return len(self.repr)

    def push(self, x):
        self.repr.append(x)

    def pop(self):
        self.repr, x = self.repr[0:-1], self.repr[-1]
        return x

    def popN(self, n):
        if n == 0:
            return None
        else:
            self.repr, x = self.repr[0:-n], self.repr[-n:]
            return x

    def empty(self):
        return self.repr == []

    def top(self):
        return self.repr[-1]

    def clone(self):
        newStack = Stack()
        newStack.repr = copy(self.repr)
        return newStack
