
def all(f, xs, initial):
    return reduce(lambda a,b: a and b, map(f, xs), initial)
