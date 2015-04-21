###
# build, install, and uninstall Jabil's Wolf Creek Debug Utility

# Write permission is required in installation directories, probably
#   /usr/local/lib/python2.7/dist-packages/
#   /usr/local/bin/
# so usually install and uninstall as root.

soffice = libreoffice

.PHONY:	all build install uninstall clean clobber

all:	build

build:	wcdu-guide.pdf
	python setup.py sdist

install:
	pip install $(shell ls -t dist/*)

uninstall:
	pip uninstall wcdu

convdir = /tmp/LibO_Conversion-$$$$
wcdu-guide.pdf :   wcdu-guide.odt
	"$(soffice)" --writer -env:UserInstallation=file://$(convdir) --invisible --headless --convert-to pdf  $<
	rm -rf $(convdir)

clean:
	-rm -rf *.pyc *~ MANIFEST build wcdu-guide.pdf

clobber:	clean
	-rm -rf dist

