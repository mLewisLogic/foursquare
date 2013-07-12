#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2013 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase



class SettingsEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_setting(self):
        response = self.api.settings(self.default_settingid)
        assert 'value' in response

    def test_all(self):
        response = self.api.settings.all()
        assert 'settings' in response
