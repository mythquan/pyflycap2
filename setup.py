try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
import os
import sys
from os.path import join, exists, dirname, abspath, isdir
from os import environ, listdir
from pyflycap2 import __version__
try:
    import Cython.Compiler.Options
    #Cython.Compiler.Options.annotate = True
    from Cython.Distutils import build_ext
    have_cython = True
    cmdclass = {'build_ext': build_ext}
except ImportError:
    have_cython = False
    cmdclass = {}
if os.name=='posix':
    include_dirs='/usr/include/flycapture'
    libraries='flycapture-c'
    library_dirs='/usr/lib'
    data_files=[]

mods = ['interface']
extra_compile_args = ["-O2", '-fno-strict-aliasing']
mod_suffix = '.pyx' if have_cython else '.c'
    

ext_modules = [Extension(
    'pyflycap2.' + src_file,
    sources=[join('pyflycap2', src_file + mod_suffix)],
    libraries=['flycapture-c', 'flycapturegui-c'],
    include_dirs=[include_dirs], library_dirs=[library_dirs],
    extra_compile_args=extra_compile_args) for src_file in mods]



setup(
    name='pyflycap2',
    version=__version__,
    author='Matthew Einhorn',
    license='MIT',
    description='Cython bindings for Point Gray Fly Capture 2.',
    url='http://matham.github.io/pyflycap2/',
    packages=['pyflycap2'],
    data_files=data_files,
    cmdclass=cmdclass, ext_modules=ext_modules)

