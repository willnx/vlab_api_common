clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-find . -name '*.pyc' -delete
	-rm -f tests/.coverage

build: clean
	python setup.py bdist_wheel --universal

install: uninstall build
	pip install -U dist/*.whl

uninstall:
	-python uninstall -y vlab-api-common

test: uninstall install
	cd tests && nosetests -v --with-coverage --cover-package=vlab_api_common
