#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class SpecialsEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_special(self):
        response = self.api.specials(self.default_specialid, {'venueId': self.default_special_venueid})
        assert 'special' in response

    def test_search(self):
        response = self.api.specials.search({'ll': self.default_geo})
        assert 'specials' in response

    def test_search_limit(self):
        response = self.api.specials.search({'ll': self.default_geo, 'limit': 10})
        assert 'specials' in response



class SpecialsUserlessEndpointTestCase(BaseUserlessEnpdointTestCase):
    """
    General
    """
    def test_special(self):
        response = self.api.specials(self.default_specialid, {'venueId': self.default_special_venueid})
        assert 'special' in response

    def test_search(self):
        response = self.api.specials.search({'ll': self.default_geo})
        assert 'specials' in response

    def test_search_limit(self):
        response = self.api.specials.search({'ll': self.default_geo, 'limit': 10})
        assert 'specials' in response
