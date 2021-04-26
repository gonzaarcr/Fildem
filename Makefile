
version = `python3 -c "import fildem; print(fildem.__version__)"`

build:
	# python3 setup.py bdist_wheel
	python3 setup.py install --root=debian --install-layout=deb --no-compile
	cd debian && find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums && cd -
	sed -i "s/Version: .*/Version: $(version)/" "debian/DEBIAN/control" 
	dpkg -b debian/ fildem_$(version)_all.deb

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf debian/usr/
	rm debian/DEBIAN/md5sums
