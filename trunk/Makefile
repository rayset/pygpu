

all:

doc: pygpu/*.py pygpu/*/*.py 
	tools/pythondoc.py -f -Dstyle=pygpu-doc.css fluid.py pygpu
	mv pythondoc-*.html doc

dist: clean-pyc MANIFEST
	python setup.py sdist --formats=zip

MANIFEST: 
	sh make-manifest.sh > MANIFEST

clean: clean-pyc
	rm -rf .cg_cache dist build

clean-pyc:
	rm -f `find -name "*.pyc"`

.PHONY: clean-pyc MANIFEST doc