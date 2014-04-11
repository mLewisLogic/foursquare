#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2013 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase

import os

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')


class PhotosEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_photo(self):
        response = self.api.photos(self.default_photoid)
        assert 'photo' in response

    def test_attach_photo(self):
        """Creates a checkin and attaches a photo to it."""
        response = self.api.checkins.add(params={'venueId': self.default_venueid})
        checkin = response.get('checkin')
        self.assertNotEqual(checkin, None)

        photo_data = open(os.path.join(TEST_DATA_DIR, 'test-photo.jpg'), 'rb')
        try:
            response = self.api.photos.add(params={'checkinId': checkin['id']},
                    photo_data=photo_data)
            photo = response.get('photo')
            self.assertNotEqual(photo, None)
            self.assertEquals(300, photo['width'])
            self.assertEquals(300, photo['height'])
        finally:
            photo_data.close()
