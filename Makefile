
build:
	# python3 setup.py bdist_wheel
	python3 setup.py install --root=debian --install-layout=deb --no-compile
	cd debian && find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums && cd -
	dpkg -b debian/ fildem_0.6.5_all.deb

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf debian/usr/
	rm debian/DEBIAN/md5sums
