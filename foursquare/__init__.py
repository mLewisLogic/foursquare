#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

try:
    import simplejson as json
except ImportError:
    import json

import cStringIO as StringIO
import inspect
import math
import time
import urllib

# 3rd party libraries that might not be present during initial install
#  but we need to import for the version #
try:
    import httplib2
    import poster
except ImportError:
    pass




# Default API version. Move this forward as the library is maintained and kept current
API_VERSION = '20120418'

# Library versioning matches supported foursquare API version
__version__ = API_VERSION
__author__ = u'Mike Lewis'

AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authenticate'
TOKEN_ENDPOINT = 'https://foursquare.com/oauth2/access_token'
API_ENDPOINT = 'https://api.foursquare.com/v2'

# Number of times to retry http requests
NUM_REQUEST_RETRIES = 3

# Max number of sub-requests per multi request
MAX_MULTI_REQUESTS = 5


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
            return '{AUTH_ENDPOINT}?{params}'.format(
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
            # Get the response from the token uri and attempt to parse
            response = _request_with_retry(url)
            return response.get('access_token')


    class Requester(object):
        """Api requesting object"""
        def __init__(self, client_id=None, client_secret=None, access_token=None, version=None):
            """Sets up the api object"""
            self.client_id = client_id
            self.client_secret = client_secret
            self.set_token(access_token)
            self.version = version if version else API_VERSION
            self.multi_requests = list()

        def set_token(self, access_token):
            """Set the OAuth token for this requester"""
            self.oauth_token = access_token
            self.userless = not bool(access_token) # Userless if no access_token

        def GET(self, path, params={}, **kwargs):
            """GET request that returns processed data"""
            # Short-circuit multi requests
            if kwargs.get('multi') is True:
                return self.add_multi_request(path, params)
            # Continue processing normal requests
            params = self._enrich_params(params)
            url = '{API_ENDPOINT}{path}?{params}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path,
                params=urllib.urlencode(params)
            )
            return self._request(url)

        def add_multi_request(self, path, params={}):
            """Add multi request to list and return the number of requests added"""
            url = '{path}?{params}'.format(
                path=path,
                params=urllib.urlencode(params)
            )
            self.multi_requests.append(url)
            return len(self.multi_requests)

        def POST(self, path, params={}):
            """POST request that returns processed data"""
            params = self._enrich_params(params)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            return self._request(url, params)

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

        def venuehistory(self, USER_ID=u'self', params={}, multi=False):
            """https://developer.foursquare.com/docs/users/venuehistory"""
            return self.GET('{USER_ID}/venuehistory'.format(USER_ID=USER_ID), params, multi=multi)

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

        def update(self, params):
            """https://developer.foursquare.com/docs/users/update"""
            return self.POST('self/update', params)




    class Venues(_Endpoint):
        """Venue specific endpoint"""
        endpoint = 'venues'

        """
        General
        """
        def __call__(self, VENUE_ID, multi=False):
            """https://developer.foursquare.com/docs/venues/venues"""
            return self.GET('{VENUE_ID}'.format(VENUE_ID=VENUE_ID), multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/venues/add"""
            return self.POST('add', params)

        def categories(self, multi=False):
            """https://developer.foursquare.com/docs/venues/categories"""
            return self.GET('categories', multi=multi)

        def explore(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/explore"""
            return self.GET('explore', params, multi=multi)

        MAX_SEARCH_LIMIT = 50
        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/search"""
            return self.GET('search', params, multi=multi)

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

        def tips(self, VENUE_ID, params={}, multi=False):
            """https://developer.foursquare.com/docs/venues/tips"""
            return self.GET('{VENUE_ID}/tips'.format(VENUE_ID=VENUE_ID), params, multi=multi)

        """
        Actions
        """
        def flag(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/flag"""
            return self.POST('{VENUE_ID}/edit'.format(VENUE_ID=VENUE_ID), params)

        def marktodo(self, VENUE_ID, params={}):
            """https://developer.foursquare.com/docs/venues/edit"""
            return self.POST('{VENUE_ID}/edit'.format(VENUE_ID=VENUE_ID), params)

        def proposeedit(self, VENUE_ID, params):
            """https://developer.foursquare.com/docs/venues/proposeedit"""
            return self.POST('{VENUE_ID}/proposeedit'.format(VENUE_ID=VENUE_ID), params)


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

        def deletecomment(self, CHECKIN_ID, params):
            """https://developer.foursquare.com/docs/checkins/deletecomment"""
            return self.POST('{CHECKIN_ID}/deletecomment'.format(CHECKIN_ID=CHECKIN_ID), params)


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
            return self.GET('{LIST_ID}/suggestphoto'.format(LIST_ID=LIST_ID), params, multi=multi)

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

        def add(self, photo_data, params):
            """https://developer.foursquare.com/docs/photos/add"""
            params['photo'] = poster.encode.MultipartParam(
                name='photo',
                filename='photo',
                filetype='image/jpeg',
                fileobj=StringIO.StringIO(photo_data)
            )
            return self.POST('add', params)


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

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/pages/search"""
            return self.GET('search', params, multi=multi)

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

            note: This generator with yield both data, and FoursquareException's
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
                        _check_response(response)
                        yield response['response']
                    except FoursquareException, e:
                        yield e

        @property
        def num_required_api_calls(self):
            """Returns the expected number of API calls to process"""
            return int(math.ceil(len(self.requester.multi_requests) / float(MAX_MULTI_REQUESTS)))



"""
Network helper functions
"""
def _request_with_retry(url, data=None):
    """Tries to load data from an endpoint using retries"""
    for i in xrange(NUM_REQUEST_RETRIES):
        try:
            return _process_request_with_httplib2(url, data)
        except FoursquareException, e:
            # Some errors don't bear repeating
            if e.__class__ in [InvalidAuth, ParamError, EndpointError, NotAuthorized, Deprecated]: raise
            if ((i + 1) == NUM_REQUEST_RETRIES): raise
        time.sleep(1)

def _process_request_with_httplib2(url, data=None):
    """Make the request and handle exception processing"""
    h = httplib2.Http()
    try:
        if data:
            datagen, headers = poster.encode.multipart_encode(data)
            data = ''.join(datagen)
            method = 'POST'
        else:
            headers = {}
            method = 'GET'
        response, body = h.request(url, method, headers=headers, body=data)
        data = _json_to_data(body)
        # Default case, Got proper response
        if response.status == 200:
            return data
        return _check_response(data)
    except httplib2.HttpLib2Error, e:
        log.error(e)
        raise FoursquareException(u'Error connecting with foursquare API')

def _json_to_data(s):
    """Convert a response string to data"""
    try:
        return json.loads(s)
    except ValueError, e:
        log.error('Invalid response: {0}'.format(e))
        raise FoursquareException(e)

def _check_response(data):
    """Processes the response data"""
    # Check the meta-data for why this request failed
    meta = data.get('meta')
    if meta:
        if meta.get('code') == 200: return data
        exc = error_types.get(meta.get('errorType'))
        if exc:
            raise exc(meta.get('errorDetail'))
        else:
            log.error(u'Unknown error type: {0}'.format(meta.get('errorType')))
            raise FoursquareException(meta.get('errorDetail'))
    else:
        log.error(u'Response format invalid, missing meta property') # body is printed in warning above
        raise FoursquareException('Missing meta')
