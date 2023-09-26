MKFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
VENVDIR = venv
VENVACTIVATE = $(VENVDIR)/bin/activate
XFCP_DIR = $(MKFILE_DIR)/
PYTHON_VERSION=$(shell python3 -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)")

.PHONY: xfcp

venv: $(VENVACTIVATE)

xfcp: venv
	. $(VENVACTIVATE) && \
	pip install $(XFCP_DIR)

$(VENVACTIVATE): requirements.txt
	test -d $(VENVDIR) || python3 -m venv $(VENVDIR) --copies
	. $(VENVACTIVATE) && \
	pip3 install wheel && \
	pip3 install -r requirements.txt && \
	touch $(VENVACTIVATE)

clean:
	rm -rf __pycache__

mrproper: clean
	rm -rf $(VENVDIR)
