#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2014 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase



class CheckinsEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_checkin(self):
        response = self.api.checkins.add(params={'venueId': self.default_venueid})
        assert 'checkin' in response

    def test_recent(self):
        response = self.api.checkins.recent()
        assert 'recent' in response

    def test_recent_location(self):
        response = self.api.checkins.recent(params={'ll': self.default_geo})
        assert 'recent' in response

    def test_recent_limit(self):
        response = self.api.checkins.recent(params={'limit': 10})
        assert 'recent' in response
