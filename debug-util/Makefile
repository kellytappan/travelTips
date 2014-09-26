###
# build, install, and uninstall Jabil's Wolf Creek Debug Utility

# Write permission is required in installation directories, probably
#   /usr/local/lib/python2.7/dist-packages/
#   /usr/local/bin/
# so usually install and uninstall as root.

.PHONY:	build install uninstall

build:
	python setup.py sdist

install:
	pip install $(shell ls -tr dist/*)

uninstall:
	pip uninstall wcdu
