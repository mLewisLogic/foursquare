#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2013 Mike Lewis

import os
import unittest

import foursquare

if 'CLIENT_ID' in os.environ and 'CLIENT_SECRET' in os.environ and 'ACCESS_TOKEN' in os.environ:
    CLIENT_ID = os.environ['CLIENT_ID']
    CLIENT_SECRET = os.environ['CLIENT_SECRET']
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
else:
    try:
        from _creds import *
    except ImportError:
        print "Please create a creds.py file in this package, based upon creds.example.py"



class BaseEndpointTestCase(unittest.TestCase):
    default_geo = u'40.7,-74.0'
    default_geo_radius = 100
    default_userid = u'1070527'
    default_venueid = u'40a55d80f964a52020f31ee3'
    default_checkinid = u'51019f65e4b07f82620061f7'
    default_tipid = u'4b5e662a70c603bba7d790b4'
    default_listid = u'self/tips'
    default_photoid = u'4d0fb8162d39a340637dc42b'
    default_settingid = u'receivePings'
    default_specialid = u'4e0debea922e6f94b1410bb7'
    default_special_venueid = u'4e0deab3922e6f94b1410af3'
    default_eventid = u'4e173d2cbd412187aabb3c04'
    default_pageid = u'1070527'

class BaseAuthenticationTestCase(BaseEndpointTestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri='http://example.org'
        )

class BaseAuthenticatedEndpointTestCase(BaseEndpointTestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            access_token=ACCESS_TOKEN
        )

class BaseUserlessEndpointTestCase(BaseEndpointTestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            access_token=ACCESS_TOKEN
        )

class MultilangEndpointTestCase(BaseEndpointTestCase):
    def setUp(self):
        self.apis = []
        for lang in ('es', 'fr', 'de', 'it', 'ja', 'th', 'ko', 'ru', 'pt', 'id'):
            self.apis.append(
                foursquare.Foursquare(
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET,
                    lang=lang
                )
            )