#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2013 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase



class PhotosEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_photo(self):
        response = self.api.photos(self.default_photoid)
        assert 'photo' in response
