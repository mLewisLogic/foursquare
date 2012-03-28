#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class EventsEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_event(self):
        response = self.api.events(self.default_eventid)
        assert 'event' in response


    def test_categories(self):
        response = self.api.events.categories()
        assert 'categories' in response


    def test_search(self):
        response = self.api.events.search({'domain': u'songkick.com', 'eventId': u'8183976'})
        assert 'events' in response



class EventsUserlessEndpointTestCase(BaseUserlessEnpdointTestCase):
    """
    General
    """
    def test_categories(self):
        response = self.api.events.categories()
        assert 'categories' in response


    def test_search(self):
        response = self.api.events.search({'domain': u'songkick.com', 'eventId': u'8183976'})
        assert 'events' in response
