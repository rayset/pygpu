
import sys, os
from distutils.core import setup

baseVersion = "0.2.0a"
revision=""
for line in os.popen("svn info"):
    words = line.split()
    if len(words) == 0:
        continue
    elif words[0] == "Revision:":
        revision = "-" + words[1]

setup(name='PyGPU',
      version=baseVersion+revision,
      description='PyGPU - Python programming for the GPU',
      author='Calle Lejdfors',
      author_email='calle.lejdfors@cs.lth.se',
      url='http://www.cs.lth.se/~calle/pygpu',
      packages=['pygpu', 'pygpu.compiler', 'pygpu.backends',
                'pygpu.GPU', 'pygpu.utils'],
      ext_modules=[],
      )

