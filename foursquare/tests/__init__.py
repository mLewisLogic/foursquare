#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis

import unittest

import foursquare

try:
    from . import _creds
except ImportError:
    print "Please create a creds.py file in this package, based upon creds.example.py"



class BaseEnpdointTestCase(unittest.TestCase):
    default_geo = u'40.7,-74.0'
    default_geo_radius = 100
    default_userid = u'1070527'
    default_venueid = u'40a55d80f964a52020f31ee3'
    default_checkinid = u'4d627f6814963704dc28ff94'
    default_tipid = u'4b5e662a70c603bba7d790b4'
    default_listid = u'self/dones'
    default_photoid = u'4d0fb8162d39a340637dc42b'
    default_settingid = u'receivePings'
    default_specialid = u'4e0debea922e6f94b1410bb7'
    default_special_venueid = u'4e0deab3922e6f94b1410af3'
    default_eventid = u'4e173d2cbd412187aabb3c04'
    default_pageid = u'1070527'

class BaseAuthenticationTestCase(BaseEnpdointTestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=_creds.CLIENT_ID,
            client_secret=_creds.CLIENT_SECRET,
            redirect_uri=_creds.REDIRECT_URI
        )

class BaseAuthenticatedEnpdointTestCase(BaseEnpdointTestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=_creds.CLIENT_ID,
            client_secret=_creds.CLIENT_SECRET,
            access_token=_creds.ACCESS_TOKEN
        )

class BaseUserlessEnpdointTestCase(BaseEnpdointTestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=_creds.CLIENT_ID,
            client_secret=_creds.CLIENT_SECRET,
            access_token=_creds.ACCESS_TOKEN
        )
