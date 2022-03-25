from setuptools import setup, find_packages
from distutils.core import setup, Extension
import re
import platform

VERSIONFILE="aardwolf/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

rle_module = Extension('rle',
	define_macros = [('MAJOR_VERSION', '1'), ('MINOR_VERSION', '0')],
	include_dirs = ['/usr/local/include'],
	library_dirs = ['/usr/local/lib'],
	sources = ['aardwolf/utils/rle/rle.c']
)

setup(
	# Application name:
	name="aardwolf",

	# Version number (initial):
	version=verstr,

	# Application author details:
	author="Tamas Jos",
	author_email="info@skelsecprojects.com",

	# Packages
	packages=find_packages(),

	# Include additional files into the package
	include_package_data=True,


	# Details
	url="https://github.com/skelsec/aardwolf",

	zip_safe = False,
	#
	# license="LICENSE.txt",
	description="Asynchronous RDP protocol implementation",

	# long_description=open("README.txt").read(),
	python_requires='>=3.7',
	
	ext_modules = [rle_module],


	install_requires=[
		'minikerberos>=0.2.20',
		'winsspi>=0.0.9',
		'asysocks>=0.1.7',
		'tqdm',
		'colorama',
		'asn1crypto',
		'asn1tools',
		'pyperclip>=1.8.2',
		'arc4>=0.0.4', #faster than cryptodome
		'Pillow>=9.0.0',
		'unicrypto>=0.0.4',
	],
	
	
	classifiers=[
		"Programming Language :: Python :: 3.8",
		"Operating System :: OS Independent",
	],
	entry_points={
		'console_scripts': [
			'aardpcapsscan = aardwolf.examples.aardpcapscan:main',
			'aardploginscan = aardwolf.examples.aardploginscan:main',
			'aardpscreenshot = aardwolf.examples.aardpscreenshot:main',
		],

	}
)
