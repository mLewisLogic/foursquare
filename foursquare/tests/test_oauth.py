#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2011 Mike Lewis
import logging; log = logging.getLogger(__name__)



class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.api = foursquare.Foursquare(
            client_id=_creds.CLIENT_ID,
            client_secret=_creds.CLIENT_SECRET,
            redirect_uri=_creds.REDIRECT_URI
        )

    def test_auth_url(self):
        url = self.api.oauth.auth_url()
        assert isinstance(url, basestring)

    def test_get_token(self):
        # Honestly, not much we can do to test here
        pass
