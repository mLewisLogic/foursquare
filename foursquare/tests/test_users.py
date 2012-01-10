#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase



class UsersEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_user(self):
        response = self.api.users()
        assert 'user' in response

    def test_leaderboard(self):
        response = self.api.users.leaderboard()
        assert 'leaderboard' in response

    def test_leaderboard_limit(self):
        response = self.api.users.leaderboard({'neighbors': 5})
        assert 'leaderboard' in response

    def test_search_twitter(self):
        response = self.api.users.search({'twitter': u'mLewisLogic'})
        assert 'results' in response

    def test_search_name(self):
        response = self.api.users.search({'name': u'Mike'})
        assert 'results' in response

    def test_requests(self):
        response = self.api.users.requests()
        assert 'requests' in response

    """
    Aspects
    """
    def test_badges(self):
        response = self.api.users.badges()
        assert 'sets' in response
        assert 'badges' in response

    def test_checkins(self):
        response = self.api.users.checkins()
        assert 'checkins' in response

    def test_checkins_limit(self):
        response = self.api.users.checkins(params={'limit': 10})
        assert 'checkins' in response

    def test_checkins_offset(self):
        response = self.api.users.checkins(params={'offset': 3})
        assert 'checkins' in response

    def test_all_checkins(self):
        checkins = list(self.api.users.all_checkins())
        assert isinstance(checkins, list)

    def test_friends(self):
        response = self.api.users.friends()
        assert 'friends' in response

    def test_friends_limit(self):
        response = self.api.users.friends(params={'limit': 10})
        assert 'friends' in response

    def test_friends_offset(self):
        response = self.api.users.friends(params={'offset': 3})
        assert 'friends' in response

    def test_lists(self):
        response = self.api.users.lists()
        assert 'lists' in response

    def test_lists_friends(self):
        response = self.api.users.lists(params={'group': u'friends'})
        assert 'lists' in response

    def test_lists_suggested(self):
        response = self.api.users.lists(params={'group': u'suggested', 'll': self.default_geo})
        assert 'lists' in response

    def test_mayorships(self):
        response = self.api.users.mayorships()
        assert 'mayorships' in response

    def test_photos(self):
        response = self.api.users.photos()
        assert 'photos' in response

    def test_photos_limit(self):
        response = self.api.users.photos(params={'limit': 10})
        assert 'photos' in response

    def test_photos_offset(self):
        response = self.api.users.photos(params={'offset': 3})
        assert 'photos' in response

    def test_venuehistory(self):
        response = self.api.users.venuehistory()
        assert 'venues' in response
