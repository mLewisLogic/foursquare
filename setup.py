#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2020 Mike Lewis

import setuptools

import foursquare

version = str(foursquare.__version__)

setuptools.setup(
    name="foursquare",
    version=version,
    author="Mike Lewis",
    author_email="mlewis.mail@gmail.com",
    url="http://github.com/mLewisLogic/foursquare",
    description="easy-as-pie foursquare API client",
    long_description=open("./README.txt", "r").read(),
    download_url="http://github.com/mLewisLogic/foursquare/tarball/master",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
    ],
    packages=setuptools.find_packages(),
    install_requires=["requests>=2.1", "six"],
    license="MIT License",
    keywords="foursquare api",
    include_package_data=True,
    zip_safe=True,
)
