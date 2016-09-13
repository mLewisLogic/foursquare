#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2016 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase



class TipsEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_tip(self):
        response = self.api.tips(self.default_tipid)
        assert 'tip' in response


    """
    Aspects
    """
    def test_listed(self):
        response = self.api.tips.listed(self.default_tipid)
        assert 'lists' in response

    def test_listed_group(self):
        response = self.api.tips.listed(self.default_tipid, {'group': 'friends'})
        assert 'lists' in response



class TipsUserlessEndpointTestCase(BaseUserlessEndpointTestCase):
    """
    General
    """
    def test_tip(self):
        response = self.api.tips(self.default_tipid)
        assert 'tip' in response


    """
    Aspects
    """
    def test_listed(self):
        response = self.api.tips.listed(self.default_tipid)
        assert 'lists' in response

    def test_listed_group(self):
        response = self.api.tips.listed(self.default_tipid, params={'group': 'other'})
        assert 'lists' in response
