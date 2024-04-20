from setuptools import setup, find_packages
from setuptools_rust import Binding, RustExtension
import re

VERSIONFILE="aardwolf/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
	verstr = mo.group(1)
else:
	raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
	# Application name:
	name="aardwolf",

	# Version number (initial):
	version=verstr,

	# Application author details:
	author="Tamas Jos",
	author_email="info@skelsecprojects.com",

	# Packages
	packages=find_packages(include=['aardwolf.utils.rlers.src*']),

	# Include additional files into the package
	include_package_data=True,


	# Details
	url="https://github.com/skelsec/aardwolf",

	zip_safe = False,
	#
	# license="LICENSE.txt",
	description="Asynchronous RDP protocol implementation",

	# long_description=open("README.txt").read(),
	python_requires='>=3.8',
	
	rust_extensions=[RustExtension("librlers", path= "aardwolf/utils/rlers/Cargo.toml", binding=Binding.PyO3)],


	install_requires=[
		'unicrypto>=0.0.10',
		'asyauth>=0.0.16',
		'asysocks>=0.2.9',
		'tqdm',
		'colorama',
		'asn1crypto',
		'asn1tools',
		'pyperclip>=1.8.2',
		'arc4>=0.3.0', #faster than cryptodome
		'Pillow>=9.0.0',
	],
	
	classifiers=[
		"Programming Language :: Python :: 3.8",
		"Operating System :: OS Independent",
	],
	entry_points={
		'console_scripts': [
			'ardpscan = aardwolf.examples.scanners.__main__:main',
		],
	}
)
