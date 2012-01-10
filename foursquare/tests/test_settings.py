#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class SettingsEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_setting(self):
        response = self.api.settings(self.default_settingid)
        assert 'value' in response

    def test_all(self):
        response = self.api.settings.all()
        assert 'settings' in response
