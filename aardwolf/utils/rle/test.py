from distutils.core import setup, Extension

rle_module = Extension('rle',
	define_macros = [('MAJOR_VERSION', '1'), ('MINOR_VERSION', '0')],
	include_dirs = ['/usr/local/include'],
	library_dirs = ['/usr/local/lib'],
	sources = ['rle.c'])

setup (name = 'rle',
 ext_modules = [rle_module]
)