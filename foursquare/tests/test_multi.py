#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

import itertools

from . import BaseAuthenticatedEnpdointTestCase



class MultiEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_multi(self):
        """Load up a bunch of multi sub-requests and make sure they process as expected"""
        self.api.users(multi=True)
        self.api.users.leaderboard(multi=True)
        # Throw a non-multi in the middle to make sure we don't create conflicts
        user_response = self.api.users()
        assert 'user' in user_response
        # Resume loading the multi sub-requests
        self.api.users.badges(multi=True)
        self.api.users.lists(multi=True)
        self.api.venues.categories(multi=True)
        self.api.checkins.recent(multi=True)
        self.api.tips(self.default_tipid, multi=True)
        self.api.lists(self.default_listid, multi=True)
        self.api.photos(self.default_photoid, multi=True)
        # Now make sure the multi call comes back with what we want
        expected_responses = ('user', 'leaderboard', 'badges', 'lists', 'categories', 'recent', 'tip', 'list', 'photo',)
        for response, expected_response in itertools.izip(self.api.multi(), expected_responses):
            assert expected_response in response, '{0} not in response'.format(expected_response)
