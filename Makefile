clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-find . -name '*.pyc' -delete
	-rm -f tests/.coverage
	-docker rm `docker ps -a -q`
	-docker rmi `docker images -q --filter "dangling=true"`
	-docker network prune -f

build: clean
	python setup.py bdist_wheel --universal

install: uninstall build
	pip install -U dist/*.whl

uninstall:
	-python uninstall -y vlab-api-common

test: uninstall install
	cd tests && nosetests -v --with-coverage --cover-package=vlab_api_common
