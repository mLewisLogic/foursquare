#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2014 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase



class RateLimitTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_rate_limit(self):
        # A call is needed to load the value
        self.api.venues(self.default_venueid)
        assert int(self.api.rate_limit) > 0

    def test_rate_remaining(self):
        # A call is needed to load the value
        self.api.venues(self.default_venueid)
        assert int(self.api.rate_remaining) > 0
