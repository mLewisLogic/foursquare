#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2011 Mike Lewis, SpotOn, Inc.

from setuptools import setup

version = '0.1'

setup(name=u'foursquare',
      version=version,
      description='An API wrapper for Foursquare V2',
      long_description=open('./README', 'r').read(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'License :: OSI Approved :: MIT License',
          ],
      keywords='foursquare',
      author='Mike Lewis',
      author_email='mike@fondu.com',
      url='http://github.com/SpotOn/foursquare-python',
      license='MIT License',
      packages=['foursquare'],
      include_package_data=True,
      zip_safe=True,
      )
