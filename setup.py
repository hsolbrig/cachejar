try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requires = ["jsonasobj>=1.2.0"]

setup(
    name='cachejar',
    version="0.2.0",
    packages=['cachejar'],
    install_requires=requires,
    url='http://github.com/hsolbrig/cachejar',
    license='Apache License 2.0',
    author='Harold Solbrig',
    author_email='solbrig.harold@mayo.edu',
    description='File based cache for objects derived from files or urls',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7']
)

