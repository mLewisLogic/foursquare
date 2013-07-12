#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2013 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase



class ListsEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_list(self):
        response = self.api.lists(self.default_listid)
        assert 'list' in response



class ListsUserlessEndpointTestCase(BaseUserlessEndpointTestCase):
    """
    General
    """
    def test_list(self):
        response = self.api.lists(self.default_listid)
        assert 'list' in response
