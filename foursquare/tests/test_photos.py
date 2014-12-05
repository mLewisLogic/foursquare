#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2014 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import TEST_DATA_DIR, BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase

import os



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

        test_photo = os.path.join(TEST_DATA_DIR, 'test-photo.jpg')

        # Fail gracefully if we don't have a test photo on disk
        if os.path.isfile(test_photo):
            photo_data = open(test_photo, 'rb')
            try:
                response = self.api.photos.add(params={'checkinId': checkin['id']}, photo_data=photo_data)
                assert 'photo' in response
                photo = response.get('photo')
                self.assertNotEqual(photo, None)
                self.assertEquals(300, photo['width'])
                self.assertEquals(300, photo['height'])
            finally:
                photo_data.close()
        else:
            print(u"Put a 'test-photo.jpg' file in the testdata/ directory to enable this test.")
