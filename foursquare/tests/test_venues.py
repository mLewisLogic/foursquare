#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class VenuesEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_venue(self):
        response = self.api.venues(self.default_venueid)
        assert 'venue' in response


    def test_categories(self):
        response = self.api.venues.categories()
        assert 'categories' in response


    def test_explore(self):
        response = self.api.venues.explore({'ll': self.default_geo})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_radius(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'radius': 30})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_section(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'section': 'coffee'})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_query(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'query': 'donuts'})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_limit(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'limit': 10})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_intent(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'intent': 'specials'})
        assert 'keywords' in response
        assert 'groups' in response


    def test_search(self):
        response = self.api.venues.search({'ll': self.default_geo})
        assert 'venues' in response

    def test_search_query(self):
        response = self.api.venues.search({'ll': self.default_geo, 'query': 'donuts'})
        assert 'venues' in response

    def test_search_limit(self):
        response = self.api.venues.search({'ll': self.default_geo, 'limit': 10})
        assert 'venues' in response

    def test_search_browse(self):
        response = self.api.venues.search({'ll': self.default_geo, 'radius': self.default_geo_radius, 'intent': 'browse'})
        assert 'venues' in response


    def test_trending(self):
        response = self.api.venues.trending({'ll': self.default_geo})
        assert 'venues' in response

    def test_trending_limit(self):
        response = self.api.venues.trending({'ll': self.default_geo, 'limit': 10})
        assert 'venues' in response

    def test_trending_radius(self):
        response = self.api.venues.trending({'ll': self.default_geo, 'radius': 100})
        assert 'venues' in response


    """
    Aspects
    """
    def test_event(self):
        response = self.api.venues.events(self.default_venueid)
        assert 'events' in response


    def test_herenow(self):
        response = self.api.venues.herenow(self.default_venueid)
        assert 'hereNow' in response

    def test_herenow_limit(self):
        response = self.api.venues.herenow(self.default_venueid, {'limit': 10})
        assert 'hereNow' in response

    def test_herenow_offset(self):
        response = self.api.venues.herenow(self.default_venueid, {'offset': 3})
        assert 'hereNow' in response


    def test_listed(self):
        response = self.api.venues.listed(self.default_venueid)
        assert 'lists' in response

    def test_listed_group(self):
        response = self.api.venues.listed(self.default_venueid, {'group': 'friends'})
        assert 'lists' in response

    def test_listed_limit(self):
        response = self.api.venues.listed(self.default_venueid, {'limit': 10})
        assert 'lists' in response

    def test_listed_offset(self):
        response = self.api.venues.listed(self.default_venueid, {'offset': 3})
        assert 'lists' in response


    def test_photos(self):
        response = self.api.venues.photos(self.default_venueid, {'group': 'venue'})
        assert 'photos' in response

    def test_photos_limit(self):
        response = self.api.venues.photos(self.default_venueid, {'limit': 10})
        assert 'photos' in response

    def test_photos_offset(self):
        response = self.api.venues.photos(self.default_venueid, {'offset': 3})
        assert 'photos' in response


    def test_similar(self):
        response = self.api.venues.similar(self.default_venueid)
        assert 'similarVenues' in response


    def test_tips(self):
        response = self.api.venues.tips(self.default_venueid)
        assert 'tips' in response

    def test_tips_group(self):
        response = self.api.venues.tips(self.default_venueid, {'sort': 'popular'})
        assert 'tips' in response

    def test_tips_limit(self):
        response = self.api.venues.tips(self.default_venueid, {'limit': 10})
        assert 'tips' in response

    def test_tips_offset(self):
        response = self.api.venues.tips(self.default_venueid, {'offset': 3})
        assert 'tips' in response



class VenuesUserlessEndpointTestCase(BaseUserlessEnpdointTestCase):
    """
    General
    """
    def test_venue(self):
        response = self.api.venues(self.default_venueid)
        assert 'venue' in response


    def test_categories(self):
        response = self.api.venues.categories()
        assert 'categories' in response


    def test_explore(self):
        response = self.api.venues.explore({'ll': self.default_geo})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_radius(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'radius': 30})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_section(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'section': 'coffee'})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_query(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'query': 'donuts'})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_limit(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'limit': 10})
        assert 'keywords' in response
        assert 'groups' in response

    def test_explore_intent(self):
        response = self.api.venues.explore({'ll': self.default_geo, 'intent': 'specials'})
        assert 'keywords' in response
        assert 'groups' in response


    def test_search(self):
        response = self.api.venues.search({'ll': self.default_geo})
        assert 'venues' in response

    def test_search_query(self):
        response = self.api.venues.search({'ll': self.default_geo, 'query': 'donuts'})
        assert 'venues' in response

    def test_search_limit(self):
        response = self.api.venues.search({'ll': self.default_geo, 'limit': 10})
        assert 'venues' in response

    def test_search_browse(self):
        response = self.api.venues.search({'ll': self.default_geo, 'radius': self.default_geo_radius, 'intent': 'browse'})
        assert 'venues' in response


    def test_trending(self):
        response = self.api.venues.trending({'ll': self.default_geo})
        assert 'venues' in response

    def test_trending_limit(self):
        response = self.api.venues.trending({'ll': self.default_geo, 'limit': 10})
        assert 'venues' in response

    def test_trending_radius(self):
        response = self.api.venues.trending({'ll': self.default_geo, 'radius': 100})
        assert 'venues' in response


    """
    Aspects
    """
    def test_listed(self):
        response = self.api.venues.listed(self.default_venueid)
        assert 'lists' in response

    def test_listed_group(self):
        response = self.api.venues.listed(self.default_venueid, {'group': 'friends'})
        assert 'lists' in response

    def test_listed_limit(self):
        response = self.api.venues.listed(self.default_venueid, {'limit': 10})
        assert 'lists' in response

    def test_listed_offset(self):
        response = self.api.venues.listed(self.default_venueid, {'offset': 3})
        assert 'lists' in response


    def test_photos(self):
        response = self.api.venues.photos(self.default_venueid, {'group': 'venue'})
        assert 'photos' in response

    def test_photos_limit(self):
        response = self.api.venues.photos(self.default_venueid, {'limit': 10})
        assert 'photos' in response

    def test_photos_offset(self):
        response = self.api.venues.photos(self.default_venueid, {'offset': 3})
        assert 'photos' in response


    def test_tips(self):
        response = self.api.venues.tips(self.default_venueid)
        assert 'tips' in response

    def test_tips_group(self):
        response = self.api.venues.tips(self.default_venueid, {'sort': 'popular'})
        assert 'tips' in response

    def test_tips_limit(self):
        response = self.api.venues.tips(self.default_venueid, {'limit': 10})
        assert 'tips' in response

    def test_tips_offset(self):
        response = self.api.venues.tips(self.default_venueid, {'offset': 3})
        assert 'tips' in response
