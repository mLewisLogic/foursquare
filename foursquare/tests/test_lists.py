#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class ListsEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_list(self):
        response = self.api.lists(self.default_listid)
        assert 'list' in response



class ListsUserlessEndpointTestCase(BaseUserlessEnpdointTestCase):
    """
    General
    """
    def test_list(self):
        response = self.api.lists(self.default_listid)
        assert 'list' in response
