#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

try:
    import simplejson as json
except ImportError:
    import json

import contextlib
import datetime
import httplib
import re
import socket
import time
import urllib
import urllib2
import urlparse


# Default API version. Move this forward as the library is maintained and kept current
API_VERSION = u'20120126'

# Library versioning matches supported foursquare API version
__version__ = API_VERSION
__author__ = u'Mike Lewis'

AUTH_ENDPOINT = u'https://foursquare.com/oauth2/authenticate'
TOKEN_ENDPOINT = u'https://foursquare.com/oauth2/access_token'
API_ENDPOINT = u'https://api.foursquare.com/v2'

NUM_REQUEST_RETRIES = 3


# Generic foursquare exception
class FoursquareException(Exception): pass
# Specific exceptions
class InvalidAuth(FoursquareException): pass
class ParamError(FoursquareException): pass
class EndpointError(FoursquareException): pass
class NotAuthorized(FoursquareException): pass
class RateLimitExceeded(FoursquareException): pass
class Deprecated(FoursquareException): pass
class ServerError(FoursquareException): pass
class Other(FoursquareException): pass

error_types = {
    'invalid_auth': InvalidAuth,
    'param_error': ParamError,
    'endpoint_error': EndpointError,
    'not_authorized': NotAuthorized,
    'rate_limit_exceeded': RateLimitExceeded,
    'deprecated': Deprecated,
    'server_error': ServerError,
    'other': Other,
}



class Foursquare(object):
    """foursquare V2 API wrapper"""

    def __init__(self, client_id=None, client_secret=None, access_token=None, redirect_uri=None, version=None):
        """Sets up the api object"""
        # Set up OAuth
        self.oauth = self.OAuth(client_id, client_secret, redirect_uri)
        # Set up endpoints
        self.base_requester = self.Requester(client_id, client_secret, access_token, version)
        for endpoint in ['Users', 'Venues', 'Checkins', 'Tips', 'Lists', 'Photos', 'Settings', 'Specials', 'Events']:
            endpoint_obj = getattr(self, endpoint)(self.base_requester)
            setattr(self, endpoint_obj.endpoint, endpoint_obj)

    def set_access_token(self, access_token):
        """Update the access token to use"""
        self.base_requester.access_token = access_token


    class OAuth(object):
        """Handles OAuth authentication procedures and helps retrieve tokens"""
        def __init__(self, client_id, client_secret, redirect_uri):
            self.client_id = client_id
            self.client_secret = client_secret
            self.redirect_uri = redirect_uri

        def auth_url(self):
            """Gets the url a user needs to access to give up a user token"""
            data = {
                'client_id': self.client_id,
                'response_type': u'code',
                'redirect_uri': self.redirect_uri,
            }
            return u'{AUTH_ENDPOINT}?{params}'.format(
                AUTH_ENDPOINT=AUTH_ENDPOINT,
                params=urllib.urlencode(data))

        def get_token(self, code):
            """Gets the auth token from a user's response"""
            if not code:
                log.error(u'Code not provided')
                return None
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': u'authorization_code',
                'redirect_uri': self.redirect_uri,
                'code': unicode(code),
            }
            # Build the token uri to request
            url = u'{TOKEN_ENDPOINT}?{params}'.format(
                TOKEN_ENDPOINT=TOKEN_ENDPOINT,
                params=urllib.urlencode(data))
            log.debug(u'GET: {0}'.format(url))
            access_token = None
            # Get the response from the token uri and attempt to parse
            response = _request_with_retry(url)
            return response.get('access_token')


    class Requester(object):
        """Api requesting object"""
        def __init__(self, client_id=None, client_secret=None, access_token=None, version=None):
            """Sets up the api object"""
            self.client_id = client_id
            self.client_secret = client_secret
            self.oauth_token = access_token
            self.userless = not bool(access_token) # Userless if no access_token
            self.version = version if version else API_VERSION

        def GET(self, path, params={}):
            """GET request that returns processed data"""
            self._enrich_params(params)
            url = u'{API_ENDPOINT}{path}?{params}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path,
                params=urllib.urlencode(params)
            )
            return self._request(url)

        def POST(self, path, params={}):
            """POST request that returns processed data"""
            self._enrich_params(params)
            url = u'{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            data = urllib.urlencode(params)
            return self._request(url, data)

        def _enrich_params(self, params):
            """Enrich the params dict"""
            if self.version:
                params['v'] = self.version
            if self.userless:
                params['client_id'] = self.client_id
                params['client_secret'] = self.client_secret
            else:
                params['oauth_token'] = self.oauth_token
            return params

        def _request(self, url, data=None):
            """Performs the passed request and returns meaningful data"""
            log.debug(u'{method} url: {url}{data}'.format(
                method='POST' if data else 'GET',
                url=url,
                data=u'* {0}'.format(data) if data else u''))
            return _request_with_retry(url, data)['response']



    class _Endpoint(object):
        """Generic endpoint class"""
        def __init__(self, requester):
            """Stores the request function for retrieving data"""
            self.requester = requester

        def GET(self, path, *args, **kwargs):
            """Use the requester to get the data"""
            expanded_path = u'/{endpoint}/{path}'.format(endpoint=self.endpoint, path=path)
            return self.requester.GET(expanded_path, *args, **kwargs)

        def POST(self, path, *args, **kwargs):
            """Use the requester to post the data"""
            expanded_path = u'/{endpoint}/{path}'.format(endpoint=self.endpoint, path=path)
            return self.requester.POST(expanded_path, *args, **kwargs)



    class Users(_Endpoint):
        """User specific endpoint"""
        endpoint = u'users'

        def __call__(self, USER_ID=u'self'):
            """https://developer.foursquare.com/docs/users/users"""
            return self.GET(unicode(USER_ID))

        """
        General
        """
        def leaderboard(self, params={}):
            """https://developer.foursquare.com/docs/users/leaderboard"""
            return self.GET(u'leaderboard', params)

        def requests(self):
            """https://developer.foursquare.com/docs/users/requests"""
            return self.GET(u'requests')

        def search(self, params):
            """https://developer.foursquare.com/docs/users/search"""
            return self.GET(u'search', params)

        """
        Aspects
        """
        def badges(self, USER_ID=u'self'):
            """https://developer.foursquare.com/docs/users/badges"""
            return self.GET(u'{USER_ID}/badges'.format(USER_ID=USER_ID))

        def checkins(self, USER_ID=u'self', params={}):
            """https://developer.foursquare.com/docs/users/checkins"""
            return self.GET(u'{USER_ID}/checkins'.format(USER_ID=USER_ID), params)

        def all_checkins(self, USER_ID=u'self'):
            """Utility function: Get every checkin this user has ever made"""
            offset = 0
            while(True):
                checkins = self.checkins(USER_ID=USER_ID, params={'limit': 250, 'offset': offset})
                # Yield out each checkin
                for checkin in checkins['checkins']['items']:
                    yield checkin
                # Determine if we should stop here or query again
                offset += len(checkins['checkins']['items'])
                if (offset >= checkins['checkins']['count']) or (len(checkins['checkins']['items']) == 0):
                    # Break once we've processed everything
                    break

        def friends(self, USER_ID=u'self', params={}):
            """https://developer.foursquare.com/docs/users/friends"""
            return self.GET(u'{USER_ID}/friends'.format(USER_ID=USER_ID), params)

        def lists(self, USER_ID=u'self', params={}):
            """https://developer.foursquare.com/docs/users/lists"""
            return self.GET(u'{USER_ID}/lists'.format(USER_ID=USER_ID), params)

        def mayorships(self, USER_ID=u'self', params={}):
            """https://developer.foursquare.com/docs/users/mayorships"""
            return self.GET(u'{USER_ID}/mayorships'.format(USER_ID=USER_ID), params)

        def photos(self, USER_ID=u'self', params={}):
            """https://developer.foursquare.com/docs/users/photos"""
            return self.GET(u'{USER_ID}/photos'.format(USER_ID=USER_ID), params)

        def venuehistory(self, USER_ID=u'self', params={}):
            """https://developer.foursquare.com/docs/users/venuehistory"""
            return self.GET(u'{USER_ID}/venuehistory'.format(USER_ID=USER_ID), params)

        """
        Actions
        """
        def approve(self, USER_ID):
            """https://developer.foursquare.com/docs/users/approve"""
            return self.POST(u'{USER_ID}/approve'.format(USER_ID=USER_ID))

        def deny(self, USER_ID):
            """https://developer.foursquare.com/docs/users/deny"""
            return self.POST(u'{USER_ID}/deny'.format(USER_ID=USER_ID))

        def request(self, USER_ID):
            """https://developer.foursquare.com/docs/users/request"""
            return self.POST(u'{USER_ID}/request'.format(USER_ID=USER_ID))

        def setpings(self, USER_ID, params):
            """https://developer.foursquare.com/docs/users/setpings"""
            return self.POST(u'{USER_ID}/setpings'.format(USER_ID=USER_ID), params)

        def unfriend(self, USER_ID):
            """https://developer.foursquare.com/docs/users/unfriend"""
            return self.POST(u'{USER_ID}/unfriend'.format(USER_ID=USER_ID))

        def update(self, params):
            """https://developer.foursquare.com/docs/users/update"""
            return self.POST(u'self/update', params)




    class Venues(_Endpoint):
        """Venue specific endpoint"""
        endpoint = u'venues'

        """
        General
        """
        def __call__(self, VENUE_ID):
            """https://developer.foursquare.com/docs/venues/venues"""
            return self.GET(unicode(VENUE_ID))

        def add(self, params):
            """https://developer.foursquare.com/docs/venues/add"""
            return self.POST(u'add', params)

        def categories(self):
            """https://developer.foursquare.com/docs/venues/categories"""
            return self.GET(u'categories')

        def explore(self, params):
            """https://developer.foursquare.com/docs/venues/explore"""
            return self.GET(u'explore', params)

        MAX_SEARCH_LIMIT = 50
        def search(self, params):
            """https://developer.foursquare.com/docs/venues/search"""
            return self.GET(u'search', params)

        def trending(self, params):
            """https://developer.foursquare.com/docs/venues/trending"""
            return self.GET(u'trending', params)

        """
        Aspects
        """
        def events(self, VENUE_ID):
            """https://developer.foursquare.com/docs/venues/events"""
            return self.GET(u'{VENUE_ID}/events'.format(VENUE_ID=VENUE_ID))

        def herenow(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/herenow"""
            return self.GET(u'{VENUE_ID}/herenow'.format(VENUE_ID=VENUE_ID), params)

        def listed(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/listed"""
            return self.GET(u'{VENUE_ID}/listed'.format(VENUE_ID=VENUE_ID), params)

        def photos(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/photos"""
            return self.GET(u'{VENUE_ID}/photos'.format(VENUE_ID=VENUE_ID), params)

        def similar(self, VENUE_ID):
            """https://developer.foursquare.com/docs/venues/similar"""
            return self.GET(u'{VENUE_ID}/similar'.format(VENUE_ID=VENUE_ID))

        def tips(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/tips"""
            return self.GET(u'{VENUE_ID}/tips'.format(VENUE_ID=VENUE_ID), params)

        """
        Actions
        """
        def flag(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/flag"""
            return self.POST(u'{VENUE_ID}/edit'.format(VENUE_ID=VENUE_ID), params)

        def marktodo(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/edit"""
            return self.POST(u'{VENUE_ID}/edit'.format(VENUE_ID=VENUE_ID), params)

        def proposeedit(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/proposeedit"""
            return self.POST(u'{VENUE_ID}/proposeedit'.format(VENUE_ID=VENUE_ID), params)


    class Checkins(_Endpoint):
        """Checkin specific endpoint"""
        endpoint = u'checkins'

        def __call__(self, CHECKIN_ID, params={}):
            """https://developer.foursquare.com/docs/checkins/checkins"""
            return self.GET(u'{CHECKIN_ID}'.format(CHECKIN_ID=CHECKIN_ID), params)

        def add(self, params):
            """https://developer.foursquare.com/docs/checkins/add"""
            return self.POST(u'add', params)

        def recent(self, params={}):
            """https://developer.foursquare.com/docs/checkins/recent"""
            return self.GET(u'recent', params)

        """
        Actions
        """
        def addcomment(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/addcomment"""
            return self.POST(u'{CHECKIN_ID}/addcomment'.format(CHECKIN_ID=CHECKIN_ID), params)

        def deletecomment(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/deletecomment"""
            return self.POST(u'{CHECKIN_ID}/deletecomment'.format(CHECKIN_ID=CHECKIN_ID), params)


    class Tips(_Endpoint):
        """Tips specific endpoint"""
        endpoint = u'tips'

        def __call__(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/tips"""
            return self.GET(unicode(TIP_ID))

        def add(self, params):
            """https://developer.foursquare.com/docs/tips/add"""
            return self.POST(u'add', params)

        def search(self, params):
            """https://developer.foursquare.com/docs/tips/add"""
            return self.GET(u'search', params)

        """
        Aspects
        """
        def done(self, TIP_ID, params={}):
            """https://developer.foursquare.com/docs/tips/done"""
            return self.GET(u'{TIP_ID}/done'.format(TIP_ID=TIP_ID), params)

        def listed(self, TIP_ID, params={}):
            """https://developer.foursquare.com/docs/tips/listed"""
            return self.GET(u'{TIP_ID}/listed'.format(TIP_ID=TIP_ID), params)

        """
        Actions
        """
        def markdone(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/markdone"""
            return self.POST(u'{TIP_ID}/markdone'.format(TIP_ID=TIP_ID))

        def marktodo(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/marktodo"""
            return self.POST(u'{TIP_ID}/marktodo'.format(TIP_ID=TIP_ID))

        def unmark(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/unmark"""
            return self.POST(u'{TIP_ID}/unmark'.format(TIP_ID=TIP_ID))


    class Lists(_Endpoint):
        """Lists specific endpoint"""
        endpoint = u'lists'

        def __call__(self, LIST_ID, params={}):
            """https://developer.foursquare.com/docs/lists/lists"""
            return self.GET(unicode(LIST_ID), params)

        def add(self, params):
            """https://developer.foursquare.com/docs/lists/add"""
            return self.POST(u'add', params)

        """
        Aspects
        """
        def followers(self, LIST_ID):
            """https://developer.foursquare.com/docs/lists/followers"""
            return self.GET(u'{LIST_ID}/followers'.format(LIST_ID=LIST_ID))

        def suggestphoto(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/suggestphoto"""
            return self.GET(u'{LIST_ID}/suggestphoto'.format(LIST_ID=LIST_ID), params)

        def suggesttip(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/suggesttip"""
            return self.GET(u'{LIST_ID}/suggestphoto'.format(LIST_ID=LIST_ID), params)

        def suggestvenues(self, LIST_ID):
            """https://developer.foursquare.com/docs/lists/suggestvenues"""
            return self.GET(u'{LIST_ID}/suggestvenues'.format(LIST_ID=LIST_ID))

        """
        Actions
        """
        def additem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/additem"""
            return self.POST(u'{LIST_ID}/additem'.format(LIST_ID=LIST_ID), params)

        def deleteitem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/deleteitem"""
            return self.POST(u'{LIST_ID}/deleteitem'.format(LIST_ID=LIST_ID), params)

        def follow(self, LIST_ID):
            """https://developer.foursquare.com/docs/lists/follow"""
            return self.POST(u'{LIST_ID}/follow'.format(LIST_ID=LIST_ID))

        def moveitem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/moveitem"""
            return self.POST(u'{LIST_ID}/moveitem'.format(LIST_ID=LIST_ID), params)

        def share(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/share"""
            return self.POST(u'{LIST_ID}/share'.format(LIST_ID=LIST_ID), params)

        def unfollow(self, LIST_ID):
            """https://developer.foursquare.com/docs/tips/unfollow"""
            return self.POST(u'{LIST_ID}/unfollow'.format(LIST_ID=LIST_ID))

        def update(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/tips/update"""
            return self.POST(u'{LIST_ID}/update'.format(LIST_ID=LIST_ID), params)

        def updateitem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/tips/updateitem"""
            return self.POST(u'{LIST_ID}/updateitem'.format(LIST_ID=LIST_ID), params)


    class Photos(_Endpoint):
        """Photo specific endpoint"""
        endpoint = u'photos'

        def __call__(self, PHOTO_ID):
            """https://developer.foursquare.com/docs/photos/photos"""
            return self.GET(unicode(PHOTO_ID))

        def add(self, params):
            """https://developer.foursquare.com/docs/photos/add"""
            return self.POST(u'add', params)


    class Settings(_Endpoint):
        """Setting specific endpoint"""
        endpoint = u'settings'

        def __call__(self, SETTING_ID):
            """https://developer.foursquare.com/docs/settings/settings"""
            return self.GET(unicode(SETTING_ID))

        def all(self):
            """https://developer.foursquare.com/docs/settings/all"""
            return self.GET(u'all')

        """
        Actions
        """
        def set(self, SETTING_ID, params):
            """https://developer.foursquare.com/docs/settings/set"""
            return self.POST(u'{SETTING_ID}/set'.format(SETTING_ID=SETTING_ID), params)


    class Specials(_Endpoint):
        """Specials specific endpoint"""
        endpoint = u'specials'

        def __call__(self, SPECIAL_ID, params):
            """https://developer.foursquare.com/docs/specials/specials"""
            return self.GET(unicode(SPECIAL_ID), params)

        def search(self, params):
            """https://developer.foursquare.com/docs/specials/search"""
            return self.GET(u'search', params)

        """
        Actions
        """
        def flag(self, SPECIAL_ID, params):
            """https://developer.foursquare.com/docs/specials/flag"""
            return self.GET(u'{LIST_ID}/flag'.format(LIST_ID=LIST_ID), params)


    class Events(_Endpoint):
        """Events specific endpoint"""
        endpoint = u'events'

        def __call__(self, EVENT_ID):
            """https://developer.foursquare.com/docs/events/events"""
            return self.GET(unicode(EVENT_ID))

        def categories(self):
            """https://developer.foursquare.com/docs/events/categories"""
            return self.GET(u'categories')

        def search(self, params):
            """https://developer.foursquare.com/docs/events/search"""
            return self.GET(u'search', params)




"""
Network helper functions
"""
def _request_with_retry(url, data=None):
    """Tries to load data from an endpoint using retries"""
    for i in xrange(NUM_REQUEST_RETRIES):
        try:
            return _process_request(url, data)
        except FoursquareException, e:
            # Some errors don't bear repeating
            if e.__class__ in [InvalidAuth, ParamError, EndpointError, NotAuthorized, Deprecated]: raise
            if ((i + 1) == NUM_REQUEST_RETRIES): raise
        time.sleep(1)

# Helps pull the charset out of a response header
re_charset = re.compile(r'(?<=charset\=)(\w*)')
def _process_request(url, data=None):
    """Make the request and handle exception processing"""
    try:
        with contextlib.closing(urllib2.urlopen(url, data)) as request:
            encoding = 'utf-8' #default
            content_type = request.headers.get('content-type')
            if content_type:
                match_encoding = re_charset.search(content_type)
                if match_encoding:
                    encoding = match_encoding.group()
            response_body = unicode(request.read(), encoding)
            response = json.loads(response_body)
            return response
    except urllib2.HTTPError, e:
        response_body = e.read()
        response = json.loads(response_body)
        meta = response.get('meta')
        if meta:
            exc = error_types.get(meta.get('errorType'))
            if exc:
                raise exc(meta.get('errorDetail'))
            else:
                log.error(u'Unknown error type: {0}'.format(meta.get('errorType')))
                raise FoursquareException(meta.get('errorDetail'))
        else:
            log.error(response_body)
    except urllib2.URLError, e:
        log.error(e)
        raise FoursquareException(u'Error connecting with foursquare API')
    except socket.error, e:
        log.error(e)
        raise FoursquareException(u'Error connecting with foursquare API')
