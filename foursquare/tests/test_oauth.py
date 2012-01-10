#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticationTestCase



class OAuthEndpointTestCase(BaseAuthenticationTestCase):
    def test_auth_url(self):
        url = self.api.oauth.auth_url()
        assert isinstance(url, basestring)

    def test_get_token(self):
        # Honestly, not much we can do to test here
        pass
