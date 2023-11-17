MKFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
VENVDIR = venv
VENVACTIVATE = $(VENVDIR)/bin/activate
XFCP_DIR = $(MKFILE_DIR)/
PYTHON_VERSION=$(shell python3 -c "import sys; v = list(sys.version_info[:2]); print(f'{int(v[0])}.{int(v[1])}')")
ifeq ($(PYTHON_VERSION), 3.6)
$(info Python Version supported)
else ifeq ($(PYTHON_VERSION), 3.10)
$(info Python Version supported)
else
$(error Python Version not supported, the supported versions are 3.6 and 3.10)
endif

.PHONY: xfcp

venv: $(VENVACTIVATE)

xfcp: venv
	. $(VENVACTIVATE) && \
	if [ $(PYTHON_VERSION) = "3.6" ]; then \
		python setup.py install; \
	else \
		pip install $(XFCP_DIR); \
	fi \

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
