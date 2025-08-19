clean:
	rm -f -r build/
	rm -f -r dist/
	rm -f -r *.egg-info
	rm -f -r aardwolf/utils/rlers/target/
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +

publish: clean package
	python3 -m twine upload dist/*

package: clean
	python3 setup.py sdist
#	sudo docker pull quay.io/pypa/manylinux2014_x86_64
#	sudo docker run --rm -v `pwd`:/io quay.io/pypa/manylinux2014_x86_64 /io/builder/manylinux/build.sh

rebuild: clean
	python3 setup.py install

build:
	python3 setup.py install
