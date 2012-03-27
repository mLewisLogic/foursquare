#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis

from setuptools import setup, find_packages

import foursquare
version = str(foursquare.__version__)

setup(
    name=u'foursquare',
    version=version,
    author='Mike Lewis',
    author_email='mike@fondu.com',
    url='http://github.com/mLewisLogic/foursquare',
    description='easy-as-pie foursquare wrapper library',
    long_description=open('./readme.txt', 'r').read(),
    download_url='http://github.com/mLewisLogic/foursquare/tarball/master',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'License :: OSI Approved :: MIT License',
        ],
    packages=find_packages(),
    install_requires=[
        'httplib2',
        'poster'
    ],
    license='MIT License',
    keywords='foursquare api',
    include_package_data=True,
    zip_safe=True,
)
