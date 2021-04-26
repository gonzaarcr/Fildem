import setuptools

import fildem

with open('README.md', 'r') as fh:
	long_description = fh.read()

setuptools.setup(
	name='fildem',
	version=fildem.__version__,
	author='Gonzalo',
	author_email='gonzaarcr@gmail.com',
	description='Fildem Global Menu for Gnome Desktop',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/gonzaarcr/Fildem',
	packages=setuptools.find_packages(),
	data_files=[
		('share/applications', ['fildem-hud.desktop'])
	],
	install_requires=[
		'PyGObject>=3.30.0'
	],
	classifiers=[
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Operating System :: POSIX :: Linux'
	],
	project_urls={
		'Bug Reports': 'https://github.com/gonzaarcr/Fildem/issues',
		'Source': 'https://github.com/gonzaarcr/Fildem',
	},
	entry_points={
		'console_scripts': [
			'fildem = fildem.run:main',
			'fildem-hud = fildem.inithud:main'
		]
	}
)
