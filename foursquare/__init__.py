#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2014 Mike Lewis
import logging; log = logging.getLogger(__name__)

# Try to load JSON libraries in this order:
# ujson -> simplejson -> json
try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

import inspect
import math
import time
import sys

# 3rd party libraries that might not be present during initial install
#  but we need to import for the version #
try:
    import requests

    from six.moves.urllib import parse
    from six.moves import xrange
    import six

    # Monkey patch to requests' json using ujson when available;
    # Otherwise it wouldn't affect anything
    requests.models.json = json
except ImportError:
    pass


# Helpful for debugging what goes in and out
NETWORK_DEBUG = False
if NETWORK_DEBUG:
    # These two lines enable debugging at httplib level (requests->urllib3->httplib)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


# Default API version. Move this forward as the library is maintained and kept current
API_VERSION_YEAR  = '2015'
API_VERSION_MONTH = '05'
API_VERSION_DAY   = '26'
API_VERSION = '{year}{month}{day}'.format(year=API_VERSION_YEAR, month=API_VERSION_MONTH, day=API_VERSION_DAY)

# Library versioning matches supported foursquare API version
__version__ = '1!{year}.{month}.{day}'.format(year=API_VERSION_YEAR, month=API_VERSION_MONTH, day=API_VERSION_DAY)
__author__ = u'Mike Lewis'

AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authenticate'
TOKEN_ENDPOINT = 'https://foursquare.com/oauth2/access_token'
API_ENDPOINT = 'https://api.foursquare.com/v2'

# Number of times to retry http requests
NUM_REQUEST_RETRIES = 3

# Max number of sub-requests per multi request
MAX_MULTI_REQUESTS = 5

# Change this if your Python distribution has issues with Foursquare's SSL cert
VERIFY_SSL = True


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
class FailedGeocode(FoursquareException): pass
class GeocodeTooBig(FoursquareException): pass
class Other(FoursquareException): pass

error_types = {
    'invalid_auth': InvalidAuth,
    'param_error': ParamError,
    'endpoint_error': EndpointError,
    'not_authorized': NotAuthorized,
    'rate_limit_exceeded': RateLimitExceeded,
    'deprecated': Deprecated,
    'server_error': ServerError,
    'failed_geocode': FailedGeocode,
    'geocode_too_big': GeocodeTooBig,
    'other': Other,
}



class Foursquare(object):
    """foursquare V2 API wrapper"""

    def __init__(self, client_id=None, client_secret=None, access_token=None, redirect_uri=None, version=None, lang=None):
        """Sets up the api object"""
        # Set up OAuth
        self.oauth = self.OAuth(client_id, client_secret, redirect_uri)
        # Set up endpoints
        self.base_requester = self.Requester(client_id, client_secret, access_token, version, lang)
        # Dynamically enable endpoints
        self._attach_endpoints()

    def _attach_endpoints(self):
        """Dynamically attach endpoint callables to this client"""
        for name, endpoint in inspect.getmembers(self):
            if inspect.isclass(endpoint) and issubclass(endpoint, self._Endpoint) and (endpoint is not self._Endpoint):
                endpoint_instance = endpoint(self.base_requester)
                setattr(self, endpoint_instance.endpoint, endpoint_instance)

    def set_access_token(self, access_token):
        """Update the access token to use"""
        self.base_requester.set_token(access_token)

    @property
    def rate_limit(self):
        """Returns the maximum rate limit for the last API call i.e. X-RateLimit-Limit"""
        return self.base_requester.rate_limit

    @property
    def rate_remaining(self):
        """Returns the remaining rate limit for the last API call i.e. X-RateLimit-Remaining"""
        return self.base_requester.rate_remaining

    class OAuth(object):
        """Handles OAuth authentication procedures and helps retrieve tokens"""
        def __init__(self, client_id, client_secret, redirect_uri):
            self.client_id = client_id
            self.client_secret = client_secret
            self.redirect_uri = redirect_uri

        def auth_url(self):
            """Gets the url a user needs to access to give up a user token"""
            params = {
                'client_id': self.client_id,
                'response_type': u'code',
                'redirect_uri': self.redirect_uri,
            }
            return '{AUTH_ENDPOINT}?{params}'.format(
                AUTH_ENDPOINT=AUTH_ENDPOINT,
                params=parse.urlencode(params))

        def get_token(self, code):
            """Gets the auth token from a user's response"""
            if not code:
                log.error(u'Code not provided')
                return None
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': u'authorization_code',
                'redirect_uri': self.redirect_uri,
                'code': six.u(code),
            }
            # Get the response from the token uri and attempt to parse
            return _get(TOKEN_ENDPOINT, params=params)['data']['access_token']


    class Requester(object):
        """Api requesting object"""
        def __init__(self, client_id=None, client_secret=None, access_token=None, version=None, lang=None):
            """Sets up the api object"""
            self.client_id = client_id
            self.client_secret = client_secret
            self.set_token(access_token)
            self.version = version if version else API_VERSION
            self.lang = lang
            self.multi_requests = list()
            self.rate_limit = None
            self.rate_remaining = None

        def set_token(self, access_token):
            """Set the OAuth token for this requester"""
            self.oauth_token = access_token
            self.userless = not bool(access_token) # Userless if no access_token

        def GET(self, path, params={}, **kwargs):
            """GET request that returns processed data"""
            params = params.copy()
            # Short-circuit multi requests
            if kwargs.get('multi') is True:
                return self.add_multi_request(path, params)
            # Continue processing normal requests
            headers = self._create_headers()
            params = self._enrich_params(params)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            result = _get(url, headers=headers, params=params)
            self.rate_limit = result['headers']['X-RateLimit-Limit']
            self.rate_remaining = result['headers']['X-RateLimit-Remaining']
            return result['data']['response']

        def add_multi_request(self, path, params={}):
            """Add multi request to list and return the number of requests added"""
            url = path
            if params:
                # First convert the params into a query string then quote the whole string
                # so it will fit into the multi request query -as a value for the requests= query param-
                url += '?{0}'.format(parse.quote_plus(parse.urlencode(params)))
            self.multi_requests.append(url)
            return len(self.multi_requests)

        def POST(self, path, data={}, files=None):
            """POST request that returns processed data"""
            if data is not None:
                data = data.copy()
            if files is not None:
                files = files.copy()
            headers = self._create_headers()
            data = self._enrich_params(data)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            result = _post(url, headers=headers, data=data, files=files)
            self.rate_limit = result['headers']['X-RateLimit-Limit']
            self.rate_remaining = result['headers']['X-RateLimit-Remaining']
            return result['data']['response']

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

        def _create_headers(self):
            """Get the headers we need"""
            headers = {}
            # If we specified a specific language, use that
            if self.lang:
                headers['Accept-Language'] = self.lang
            return headers


    class _Endpoint(object):
        """Generic endpoint class"""
        def __init__(self, requester):
            """Stores the request function for retrieving data"""
            self.requester = requester

        def _expanded_path(self, path=None):
            """Gets the expanded path, given this endpoint"""
            return '/{expanded_path}'.format(
                expanded_path='/'.join(p for p in (self.endpoint, path) if p)
            )

        def GET(self, path=None, *args, **kwargs):
            """Use the requester to get the data"""
            return self.requester.GET(self._expanded_path(path), *args, **kwargs)

        def POST(self, path=None, *args, **kwargs):
            """Use the requester to post the data"""
            return self.requester.POST(self._expanded_path(path), *args, **kwargs)



    class Users(_Endpoint):
        """User specific endpoint"""
        endpoint = 'users'

        def __call__(self, USER_ID=u'self', multi=False):
            """https://developer.foursquare.com/docs/users/users"""
            return self.GET('{USER_ID}'.format(USER_ID=USER_ID), multi=multi)

        """
        General
        """
        def leaderboard(self, params={}, multi=False):
            """https://developer.foursquare.com/docs/users/leaderboard"""
            return self.GET('leaderboard', params, multi=multi)

        def requests(self, multi=False):
            """https://developer.foursquare.com/docs/users/requests"""
            return self.GET('requests', multi=multi)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/users/search"""
            return self.GET('search', params, multi=multi)

        """
        Aspects
        """
        def badges(self, USER_ID=u'self', multi=False):
            """https://developer.foursquare.com/docs/users/badges"""
            return self.GET('{USER_ID}/badges'.format(USER_ID=USER_ID), multi=multi)

        def checkins(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/checkins"""
            return self.GET('{USER_ID}/checkins'.format(USER_ID=USER_ID), params, multi=multi)

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

        def friends(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/friends"""
            return self.GET('{USER_ID}/friends'.format(USER_ID=USER_ID), params, multi=multi)

        def lists(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/lists"""
            return self.GET('{USER_ID}/lists'.format(USER_ID=USER_ID), params, multi=multi)

        def mayorships(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/mayorships"""
            return self.GET('{USER_ID}/mayorships'.format(USER_ID=USER_ID), params, multi=multi)

        def photos(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/photos"""
            return self.GET('{USER_ID}/photos'.format(USER_ID=USER_ID), params, multi=multi)

        def tips(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/tips"""
            return self.GET('{USER_ID}/tips'.format(USER_ID=USER_ID), params, multi=multi)

        def todos(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/todos"""
            return self.GET('{USER_ID}/todos'.format(USER_ID=USER_ID), params, multi=multi)

        def venuehistory(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/venuehistory"""
            return self.GET('{USER_ID}/venuehistory'.format(USER_ID=USER_ID), params, multi=multi)

        def venuelikes(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/venuelikes"""
            return self.GET('{USER_ID}/venuelikes'.format(USER_ID=USER_ID), params, multi=multi)

        """
        Actions
        """
        def approve(self, USER_ID):
            """https://developer.foursquare.com/docs/users/approve"""
            return self.POST('{USER_ID}/approve'.format(USER_ID=USER_ID))

        def deny(self, USER_ID):
            """https://developer.foursquare.com/docs/users/deny"""
            return self.POST('{USER_ID}/deny'.format(USER_ID=USER_ID))

        def request(self, USER_ID):
            """https://developer.foursquare.com/docs/users/request"""
            return self.POST('{USER_ID}/request'.format(USER_ID=USER_ID))

        def setpings(self, USER_ID, params):
            """https://developer.foursquare.com/docs/users/setpings"""
            return self.POST('{USER_ID}/setpings'.format(USER_ID=USER_ID), params)

        def unfriend(self, USER_ID):
            """https://developer.foursquare.com/docs/users/unfriend"""
            return self.POST('{USER_ID}/unfriend'.format(USER_ID=USER_ID))

        def update(self, params={}, photo_data=None, photo_content_type='image/jpeg'):
            """https://developer.foursquare.com/docs/users/update"""
            if photo_data:
                files = { 'photo': ('photo', photo_data, photo_content_type) }
            else:
                files = None
            return self.POST('self/update', data=params, files=files)




    class Venues(_Endpoint):
        """Venue specific endpoint"""
        endpoint = 'venues'

        """
        General
        """
        def __call__(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/venues"""
            return self.GET('{VENUE_ID}'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/venues/add"""
            return self.POST('add', params)

        def categories(self, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/categories"""
            return self.GET('categories', params, multi=multi)

        def explore(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/explore"""
            return self.GET('explore', params, multi=multi)

        def managed(self, multi=False):
            """https://developer.foursquare.com/docs/venues/managed"""
            return self.GET('managed', multi=multi)

        MAX_SEARCH_LIMIT = 50
        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/search"""
            return self.GET('search', params, multi=multi)

        def suggestcompletion(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/suggestcompletion"""
            return self.GET('suggestcompletion', params, multi=multi)

        def trending(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/trending"""
            return self.GET('trending', params, multi=multi)

        """
        Aspects
        """
        def events(self, VENUE_ID, multi=False):
            """https://developer.foursquare.com/docs/venues/events"""
            return self.GET('{VENUE_ID}/events'.format(VENUE_ID=VENUE_ID), multi=multi)

        def herenow(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/herenow"""
            return self.GET('{VENUE_ID}/herenow'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def links(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/links"""
            return self.GET('{VENUE_ID}/links'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def listed(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/listed"""
            return self.GET('{VENUE_ID}/listed'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def menu(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/menu"""
            return self.GET('{VENUE_ID}/menu'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def photos(self, VENUE_ID, params, multi=False):
            """https://developer.foursquare.com/docs/venues/photos"""
            return self.GET('{VENUE_ID}/photos'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def similar(self, VENUE_ID, multi=False):
            """https://developer.foursquare.com/docs/venues/similar"""
            return self.GET('{VENUE_ID}/similar'.format(VENUE_ID=VENUE_ID), multi=multi)

        def stats(self, VENUE_ID, multi=False):
            """https://developer.foursquare.com/docs/venues/stats"""
            return self.GET('{VENUE_ID}/stats'.format(VENUE_ID=VENUE_ID), multi=multi)

        def tips(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/tips"""
            return self.GET('{VENUE_ID}/tips'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def nextvenues(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/nextvenues"""
            return self.GET('{VENUE_ID}/nextvenues'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def likes(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/likes"""
            return self.GET('{VENUE_ID}/likes'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        def hours(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/hours"""
            return self.GET('{VENUE_ID}/hours'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        """
        Actions
        """
        def edit(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/edit"""
            return self.POST('{VENUE_ID}/edit'.format(VENUE_ID=VENUE_ID), params)

        def flag(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/flag"""
            return self.POST('{VENUE_ID}/flag'.format(VENUE_ID=VENUE_ID), params)

        def marktodo(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/marktodo"""
            return self.POST('{VENUE_ID}/marktodo'.format(VENUE_ID=VENUE_ID), params)

        def proposeedit(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/proposeedit"""
            return self.POST('{VENUE_ID}/proposeedit'.format(VENUE_ID=VENUE_ID), params)

        def setrole(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/setrole"""
            return self.POST('{VENUE_ID}/setrole'.format(VENUE_ID=VENUE_ID), params)



    class Checkins(_Endpoint):
        """Checkin specific endpoint"""
        endpoint = 'checkins'

        def __call__(self, CHECKIN_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/checkins/checkins"""
            return self.GET('{CHECKIN_ID}'.format(CHECKIN_ID=CHECKIN_ID), params, multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/checkins/add"""
            return self.POST('add', params)

        def recent(self, params={}, multi=False):
            """https://developer.foursquare.com/docs/checkins/recent"""
            return self.GET('recent', params, multi=multi)

        """
        Actions
        """
        def addcomment(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/addcomment"""
            return self.POST('{CHECKIN_ID}/addcomment'.format(CHECKIN_ID=CHECKIN_ID), params)

        def addpost(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/addpost"""
            return self.POST('{CHECKIN_ID}/addpost'.format(CHECKIN_ID=CHECKIN_ID), params)

        def deletecomment(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/deletecomment"""
            return self.POST('{CHECKIN_ID}/deletecomment'.format(CHECKIN_ID=CHECKIN_ID), params)

        def reply(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/reply"""
            return self.POST('{CHECKIN_ID}/reply'.format(CHECKIN_ID=CHECKIN_ID), params)


    class Tips(_Endpoint):
        """Tips specific endpoint"""
        endpoint = 'tips'

        def __call__(self, TIP_ID, multi=False):
            """https://developer.foursquare.com/docs/tips/tips"""
            return self.GET('{TIP_ID}'.format(TIP_ID=TIP_ID), multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/tips/add"""
            return self.POST('add', params)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/tips/add"""
            return self.GET('search', params, multi=multi)

        """
        Aspects
        """
        def done(self, TIP_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/tips/done"""
            return self.GET('{TIP_ID}/done'.format(TIP_ID=TIP_ID), params, multi=multi)

        def listed(self, TIP_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/tips/listed"""
            return self.GET('{TIP_ID}/listed'.format(TIP_ID=TIP_ID), params, multi=multi)

        """
        Actions
        """
        def markdone(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/markdone"""
            return self.POST('{TIP_ID}/markdone'.format(TIP_ID=TIP_ID))

        def marktodo(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/marktodo"""
            return self.POST('{TIP_ID}/marktodo'.format(TIP_ID=TIP_ID))

        def unmark(self, TIP_ID):
            """https://developer.foursquare.com/docs/tips/unmark"""
            return self.POST('{TIP_ID}/unmark'.format(TIP_ID=TIP_ID))


    class Lists(_Endpoint):
        """Lists specific endpoint"""
        endpoint = 'lists'

        def __call__(self, LIST_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/lists/lists"""
            return self.GET('{LIST_ID}'.format(LIST_ID=LIST_ID), params, multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/lists/add"""
            return self.POST('add', params)

        """
        Aspects
        """
        def followers(self, LIST_ID, multi=False):
            """https://developer.foursquare.com/docs/lists/followers"""
            return self.GET('{LIST_ID}/followers'.format(LIST_ID=LIST_ID), multi=multi)

        def suggestphoto(self, LIST_ID, params, multi=False):
            """https://developer.foursquare.com/docs/lists/suggestphoto"""
            return self.GET('{LIST_ID}/suggestphoto'.format(LIST_ID=LIST_ID), params, multi=multi)

        def suggesttip(self, LIST_ID, params, multi=False):
            """https://developer.foursquare.com/docs/lists/suggesttip"""
            return self.GET('{LIST_ID}/suggesttip'.format(LIST_ID=LIST_ID), params, multi=multi)

        def suggestvenues(self, LIST_ID, multi=False):
            """https://developer.foursquare.com/docs/lists/suggestvenues"""
            return self.GET('{LIST_ID}/suggestvenues'.format(LIST_ID=LIST_ID), multi=multi)

        """
        Actions
        """
        def additem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/additem"""
            return self.POST('{LIST_ID}/additem'.format(LIST_ID=LIST_ID), params)

        def deleteitem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/deleteitem"""
            return self.POST('{LIST_ID}/deleteitem'.format(LIST_ID=LIST_ID), params)

        def follow(self, LIST_ID):
            """https://developer.foursquare.com/docs/lists/follow"""
            return self.POST('{LIST_ID}/follow'.format(LIST_ID=LIST_ID))

        def moveitem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/moveitem"""
            return self.POST('{LIST_ID}/moveitem'.format(LIST_ID=LIST_ID), params)

        def share(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/lists/share"""
            return self.POST('{LIST_ID}/share'.format(LIST_ID=LIST_ID), params)

        def unfollow(self, LIST_ID):
            """https://developer.foursquare.com/docs/tips/unfollow"""
            return self.POST('{LIST_ID}/unfollow'.format(LIST_ID=LIST_ID))

        def update(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/tips/update"""
            return self.POST('{LIST_ID}/update'.format(LIST_ID=LIST_ID), params)

        def updateitem(self, LIST_ID, params):
            """https://developer.foursquare.com/docs/tips/updateitem"""
            return self.POST('{LIST_ID}/updateitem'.format(LIST_ID=LIST_ID), params)


    class Photos(_Endpoint):
        """Photo specific endpoint"""
        endpoint = 'photos'

        def __call__(self, PHOTO_ID, multi=False):
            """https://developer.foursquare.com/docs/photos/photos"""
            return self.GET('{PHOTO_ID}'.format(PHOTO_ID=PHOTO_ID), multi=multi)

        def add(self, photo_data, params, photo_content_type='image/jpeg'):
            """https://developer.foursquare.com/docs/photos/add"""
            files = { 'photo': ('photo', photo_data, photo_content_type) }
            return self.POST('add', data=params, files=files)


    class Settings(_Endpoint):
        """Setting specific endpoint"""
        endpoint = 'settings'

        def __call__(self, SETTING_ID, multi=False):
            """https://developer.foursquare.com/docs/settings/settings"""
            return self.GET('{SETTING_ID}'.format(SETTING_ID=SETTING_ID), multi=multi)

        def all(self, multi=False):
            """https://developer.foursquare.com/docs/settings/all"""
            return self.GET('all', multi=multi)

        """
        Actions
        """
        def set(self, SETTING_ID, params):
            """https://developer.foursquare.com/docs/settings/set"""
            return self.POST('{SETTING_ID}/set'.format(SETTING_ID=SETTING_ID), params)


    class Specials(_Endpoint):
        """Specials specific endpoint"""
        endpoint = 'specials'

        def __call__(self, SPECIAL_ID, params, multi=False):
            """https://developer.foursquare.com/docs/specials/specials"""
            return self.GET('{SPECIAL_ID}'.format(SPECIAL_ID=SPECIAL_ID), params, multi=multi)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/specials/search"""
            return self.GET('search', params, multi=multi)

        """
        Actions
        """
        def add(self, SPECIAL_ID, params):
            """https://developer.foursquare.com/docs/specials/add"""
            return self.POST('add', params)

        def flag(self, SPECIAL_ID, params):
            """https://developer.foursquare.com/docs/specials/flag"""
            return self.POST('{SPECIAL_ID}/flag'.format(SPECIAL_ID=SPECIAL_ID), params)


    class Events(_Endpoint):
        """Events specific endpoint"""
        endpoint = 'events'

        def __call__(self, EVENT_ID, multi=False):
            """https://developer.foursquare.com/docs/events/events"""
            return self.GET('{EVENT_ID}'.format(EVENT_ID=EVENT_ID), multi=multi)

        def categories(self, multi=False):
            """https://developer.foursquare.com/docs/events/categories"""
            return self.GET('categories', multi=multi)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/events/search"""
            return self.GET('search', params, multi=multi)


    class Pages(_Endpoint):
        """Pages specific endpoint"""
        endpoint = 'pages'

        def __call__(self, USER_ID, multi=False):
            """https://developer.foursquare.com/docs/pages/pages"""
            return self.GET('{USER_ID}'.format(USER_ID=USER_ID), multi=multi)

        def venues(self, PAGE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/pages/venues"""
            return self.GET('{PAGE_ID}/venues'.format(PAGE_ID=PAGE_ID), params, multi=multi)


    class Multi(_Endpoint):
        """Multi request endpoint handler"""
        endpoint = 'multi'

        def __len__(self):
          return len(self.requester.multi_requests)

        def __call__(self):
            """
            Generator to process the current queue of multi's

            note: This generator will yield both data and FoursquareException's
            The code processing this sequence must check the yields for their type.
            The exceptions should be handled by the calling code, or raised.
            """
            while self.requester.multi_requests:
                # Pull n requests from the multi-request queue
                requests = self.requester.multi_requests[:MAX_MULTI_REQUESTS]
                del(self.requester.multi_requests[:MAX_MULTI_REQUESTS])
                # Process the 4sq multi request
                params = {
                    'requests': ','.join(requests),
                }
                responses = self.GET(params=params)['responses']
                # ... and yield out each individual response
                for response in responses:
                    # Make sure the response was valid
                    try:
                        _raise_error_from_response(response)
                        yield response['response']
                    except FoursquareException as e:
                        yield e

        @property
        def num_required_api_calls(self):
            """Returns the expected number of API calls to process"""
            return int(math.ceil(len(self.requester.multi_requests) / float(MAX_MULTI_REQUESTS)))

def _log_and_raise_exception(msg, data, cls=FoursquareException):
  """Calls log.error() then raises an exception of class cls"""
  data = u'{0}'.format(data)
  # We put data as a argument for log.error() so error tracking systems such
  # as Sentry will properly group errors together by msg only
  log.error(u'{0}: %s'.format(msg), data)
  raise cls(u'{0}: {1}'.format(msg, data))

"""
Network helper functions
"""
def _get(url, headers={}, params=None):
    """Tries to GET data from an endpoint using retries"""
    param_string = _foursquare_urlencode(params)
    for i in xrange(NUM_REQUEST_RETRIES):
        try:
            try:
                response = requests.get(url, headers=headers, params=param_string, verify=VERIFY_SSL)
                return _process_response(response)
            except requests.exceptions.RequestException as e:
                _log_and_raise_exception('Error connecting with foursquare API', e)
        except FoursquareException as e:
            # Some errors don't bear repeating
            if e.__class__ in [InvalidAuth, ParamError, EndpointError, NotAuthorized, Deprecated]: raise
            # If we've reached our last try, re-raise
            if ((i + 1) == NUM_REQUEST_RETRIES): raise
        time.sleep(1)

def _post(url, headers={}, data=None, files=None):
    """Tries to POST data to an endpoint"""
    try:
        response = requests.post(url, headers=headers, data=data, files=files, verify=VERIFY_SSL)
        return _process_response(response)
    except requests.exceptions.RequestException as e:
        _log_and_raise_exception('Error connecting with foursquare API', e)

def _process_response(response):
    """Make the request and handle exception processing"""
    # Read the response as JSON
    try:
        data = response.json()
    except ValueError:
        _log_and_raise_exception('Invalid response', response.text)

    # Default case, Got proper response
    if response.status_code == 200:
        return { 'headers': response.headers, 'data': data }
    return _raise_error_from_response(data)

def _raise_error_from_response(data):
    """Processes the response data"""
    # Check the meta-data for why this request failed
    meta = data.get('meta')
    if meta:
        # Account for foursquare conflicts
        # see: https://developer.foursquare.com/overview/responses
        if meta.get('code') in (200, 409): return data
        exc = error_types.get(meta.get('errorType'))
        if exc:
            raise exc(meta.get('errorDetail'))
        else:
            _log_and_raise_exception('Unknown error. meta', meta)
    else:
        _log_and_raise_exception('Response format invalid, missing meta property. data', data)

def _as_utf8(s):
    try:
        return str(s)
    except UnicodeEncodeError:
        return unicode(s).encode('utf8')

def _foursquare_urlencode(query, doseq=0, safe_chars="&/,+"):
    """Gnarly hack because Foursquare doesn't properly handle standard url encoding"""
    # Original doc: http://docs.python.org/2/library/urllib.html#urllib.urlencode
    # Works the same way as urllib.urlencode except two differences -
    # 1. it uses `quote()` instead of `quote_plus()`
    # 2. it takes an extra parameter called `safe_chars` which is a string
    #    having the characters which should not be encoded.
    #
    # Courtesy of github.com/iambibhas
    if hasattr(query,"items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty,va,tb = sys.exc_info()
            raise TypeError("not a valid non-string sequence or mapping object").with_traceback(tb)

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            k = parse.quote(_as_utf8(k), safe=safe_chars)
            v = parse.quote(_as_utf8(v), safe=safe_chars)
            l.append(k + '=' + v)
    else:
        for k, v in query:
            k = parse.quote(_as_utf8(k), safe=safe_chars)
            if isinstance(v, six.string_types):
                v = parse.quote(_as_utf8(v), safe=safe_chars)
                l.append(k + '=' + v)
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    len(v)
                except TypeError:
                    # not a sequence
                    v = parse.quote(_as_utf8(v), safe=safe_chars)
                    l.append(k + '=' + v)
                else:
                    # loop over the sequence
                    for elt in v:
                        l.append(k + '=' + parse.quote(_as_utf8(elt)))
    return '&'.join(l)
