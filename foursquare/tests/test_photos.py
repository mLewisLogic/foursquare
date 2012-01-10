#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class PhotosEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_photo(self):
        response = self.api.photos(self.default_photoid)
        assert 'photo' in response
