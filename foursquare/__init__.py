#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2011 Mike Lewis
import logging; log = logging.getLogger(__name__)

try:
    import simplejson as json
except ImportError:
    import json

import contextlib
import datetime
import httplib
import re
import time
import urllib
import urllib2
import urlparse





ERROR_TYPES = {
    'invalid_auth': u'OAuth token was not provided or was invalid.',
    'param_error': u'A required parameter was missing or a parameter was malformed. This is also used if the resource ID in the path is incorrect.',
    'endpoint_error': u'The requested path does not exist.',
    'not_authorized': u'Although authentication succeeded, the acting user is not allowed to see this information due to privacy restrictions.',
    'rate_limit_exceeded': u'Rate limit for this hour exceeded.',
    'deprecated': u'Something about this request is using deprecated functionality, or the response format may be about to change.',
    'server_error': u'Server is currently experiencing issues. Check status.foursquare.com for updates.',
    'other': u'Some other type of error occurred.',
}

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



# Regular expressions for processing
re_charset = re.compile(r'(?<=charset\=)(\w*)')

class Foursquare(object):
    """foursquare V2 API wrapper"""

    def __init__(self, client_id, client_secret, token=None, version=None):
        """Sets up the api object"""
        self.requester = self.Requester(client_id, client_secret, token, version)
        self.users = self.Users(self.requester)
        self.venues = self.Venues(self.requester)
        self.checkins = self.Checkins(self.requester)
        self.tips = self.Tips(self.requester)


    """
    AUTHENTICATOR IS UNTESTED!
    """
    class Authenticator(object):
        """Handles authentication procedures and helps retrieve tokens"""
        def auth_url(self, redirect_url, mobile=False):
            """Gets the url a user needs to access to give up a user token"""
            data = {
                'client_id': self.client_id,
                'response_type': u'code',
                'redirect_uri': redirect_url
            }
            return u'{AUTH_ENDPOINT}?{params}'.format(
                AUTH_ENDPOINT=AUTH_ENDPOINT,
                params=urllib.urlencode(data))

        def get_token(self, request, redirect_url):
            """Gets the auth token from a user's response"""
            if 'code' not in request.GET:
                return False
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': u'authorization_code',
                'redirect_uri': redirect_url,
                'code': request.GET.get('code'),
            }
            url = u'{TOKEN_ENDPOINT}?{params}'.format(
                TOKEN_ENDPOINT=TOKEN_ENDPOINT,
                params=urllib.urlencode(data))
            data = read_url_with_retry(url)
            response = None
            try:
                result = json.loads(data)
                response = result.get('access_token')
            except NameError, e:
                log.error(e)
            return response


    class Requester(object):
        """Api requesting object"""
        def __init__(self, client_id, client_secret, token=None, version=None):
            """Sets up the api object"""
            self.client_id = client_id
            self.client_secret = client_secret
            self.oauth_token = token
            self.userless = not bool(token)
            if version:
                self.version = version
            else:
                self.version = datetime.date.today().strftime('%Y%m%d')

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
            log.debug(u'Requesting url: {url}{data}'.format(
                url=url,
                data=u'* {0}'.format(data) if data else u''))
            return self._request_with_retry(url, data)

        def _request_with_retry(self, url, data=None):
            """Tries to load data from an endpoint using retries"""
            for i in xrange(NUM_REQUEST_RETRIES):
                try:
                    return self._process_request(url, data)
                except FoursquareException, e:
                    # Some errors don't bear repeating
                    if e.__class__ in [InvalidAuth, ParamError, EndpointError, NotAuthorized, Deprecated]: raise
                    if ((i + 1) == NUM_REQUEST_RETRIES): raise
                time.sleep(1)

        def _process_request(self, url, data=None):
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
                    return response['response']
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



    class _Endpoint(object):
        """Generic endpoint class"""
        def __init__(self, requester):
            """Stores the request function for retrieving data"""
            self.GET = requester.GET
            self.POST = requester.POST



    class Users(_Endpoint):
        """User specific endpoint"""
        def __call__(self, USER_ID=u'self'):
            """ GET: https://developer.foursquare.com/docs/users/users.html
            Returns profile information for a given user, including selected badges and mayorships. 
            """
            return self.GET(u'/users/{USER_ID}'.format(USER_ID=USER_ID))

        def leaderboard(self, params={}):
            """ GET: https://api.foursquare.com/v2/users/leaderboard
            Returns the user's leaderboard.
                @neighbors : Number of friends' scores to return that are adjacent to your score, in ranked order.
            """
            return self.GET(u'/users/leaderboard', params)

        def search(self, params={}):
            """ GET: https://api.foursquare.com/v2/users/search
            Helps a user locate friends.
                @phone : A comma-delimited list of phone numbers to look for.
                @email : A comma-delimited list of email addresses to look for.
                @twitter : A comma-delimited list of Twitter handles to look for.
                @twitterSource : A single Twitter handle. Results will be friends of this user who use foursquare.
                @fbid : A comma-delimited list of Facebook ID's to look for.
                @name : A single string to search for in users' names.
            """
            return self.GET(u'/users/search', params)

        def requests(self):
            """ GET: https://api.foursquare.com/v2/users/requests
            Shows a user the list of users with whom they have a pending friend request
            (i.e., someone tried to add the acting user as a friend, but the acting user has not accepted).
            """
            return self.GET(u'/users/requests')

        def badges(self, USER_ID=u'self'):
            """ GET: https://api.foursquare.com/v2/users/USER_ID/badges
            Returns badges for a given user.
            """
            return self.GET(u'/users/{USER_ID}/badges'.format(USER_ID=USER_ID))

        def checkins(self, USER_ID=u'self', params={}):
            """ GET: https://api.foursquare.com/v2/users/USER_ID/checkins
            Returns a history of checkins for the authenticated user.
            Currently only 'self' is supported for USER_ID.
                @limit : Number of results to return, up to 250.
                @offset : Used to page through results.
                @afterTimestamp : Retrieve the first results to follow these seconds since epoch.
                @beforeTimestamp : Retrieve the first results prior to these seconds since epoch.
            """
            return self.GET(u'/users/{USER_ID}/checkins'.format(USER_ID=USER_ID), params)

        def all_checkins(self):
            """Utility function: Get every checkin this user has ever made"""
            offset = 0
            while(True):
                checkins = self.checkins(params={'limit': 250, 'offset': offset})
                # Yield out each checkin
                for checkin in checkins['checkins']['items']:
                    yield checkin
                # Determine if we should stop here or query again
                offset += len(checkins['checkins']['items'])
                if (offset >= checkins['checkins']['count']) or (len(checkins['checkins']['items']) == 0):
                    # Break once we've processed everything
                    break

        def friends(self, USER_ID=u'self', params={}):
            """ GET: https://api.foursquare.com/v2/users/USER_ID/friends
            Returns an array of a user's friends.
                @limit : Number of results to return, up to 500.
                @offset : Used to page through results.
            """
            return self.GET(u'/users/{USER_ID}/friends'.format(USER_ID=USER_ID), params)

        def tips(self, USER_ID=u'self', params={}):
            """ GET: https://api.foursquare.com/v2/users/USER_ID/tips
            Returns tips from a user.
                @sort : One of recent, nearby, or popular. Nearby requires geolat and geolong to be provided.
                @ll : Latitude and longitude of the user's location. (comma separated)
                @limit : Number of results to return, up to 500.
                @offset : Used to page through results.
            """
            return self.GET(u'/users/{USER_ID}/tips'.format(USER_ID=USER_ID), params)

        def todos(self, USER_ID=u'self', params={}):
            """ GET: https://api.foursquare.com/v2/users/USER_ID/todos
            Returns todos from a user.
                @sort : One of recent or popular. Nearby requires geolat and geolong to be provided.
                @ll : Latitude and longitude of the user's location. (comma separated)
            """
            return self.GET(u'/users/{USER_ID}/todos'.format(USER_ID=USER_ID), params)

        def venuehistory(self, USER_ID=u'self', params={}):
            """ GET: https://api.foursquare.com/v2/users/USER_ID/venuehistory
            Returns a list of all venues visited by the specified user, along with how many visits and when they were last there.
            Currently only 'self' is supported for USER_ID.
                @afterTimestamp : Retrieve the first results to follow these seconds since epoch.
                @beforeTimestamp : Retrieve the first results prior to these seconds since epoch.
            """
            return self.GET(u'/users/{USER_ID}/venuehistory'.format(USER_ID=USER_ID), params)



    class Venues(_Endpoint):
        """Venue specific endpoint"""
        def __call__(self, VENUE_ID):
            """ GET: https://api.foursquare.com/v2/venues/VENUE_ID
            Gives details about a venue, including location, mayorship, tags, tips, specials, and category.
            Authenticated users will also receive information about who is here now.
            """
            return self.GET(u'/venues/{VENUE_ID}'.format(VENUE_ID=VENUE_ID))

        def add(self, params):
            """ POST: https://api.foursquare.com/v2/venues/add
            Allows users to add a new venue.
            """
            return self.POST(u'/venues/add', params)

        def categories(self):
            """ GET: https://api.foursquare.com/v2/venues/categories
            Returns a hierarchical list of categories applied to venues. By default, top-level categories do not have IDs.
            """
            return self.GET(u'/venues/categories')

        def explore(self, params):
            """ GET: https://api.foursquare.com/v2/venues/explore
            Returns a list of recommended venues near the current location.
                @ll : [required] Latitude and longitude of the user's location, so response can include distance.
                @llAcc : Accuracy of latitude and longitude, in meters.
                @alt : Altitude of the user's location, in meters.
                @altAcc : Accuracy of the user's altitude, in meters.
                @radius : Radius to search within, in meters.
                @section : One of food, drinks, coffee, shops, or arts.
                           Choosing one of these limits results to venues with categories matching these terms.
                @query : A search term to be applied against tips, category, tips, etc. at a venue.
                @limit : Number of results to return, up to 50.
                @basis : If present and set to friends or me, limits results to only places
                         where friends have visited or user has visited, respectively.
            """
            return self.GET(u'/venues/explore', params)

        def search(self, params):
            """ GET: https://api.foursquare.com/v2/venues/search
            Returns a list of venues near the current location, optionally matching the search term.
                @ll : [required] Latitude and longitude of the user's location, so response can include distance.
                @llAcc : Accuracy of latitude and longitude, in meters. (Does not currently affect search results.)
                @alt : Altitude of the user's location, in meters.
                @altAcc : Accuracy of the user's altitude, in meters. (Does not currently affect search results.)
                @query : A search term to be applied against titles.
                @limit : Number of results to return, up to 50.
                @intent : Indicates your intent in performing the search.
                @categoryId : A category to limit results to.
                @url : A third-party URL which we will attempt to match against our map of venues to URLs.
                @providerId : Identifier for a known third party that is part of our map of venues to URLs, used in conjunction with linkedId.
                @linkedId : Identifier used by third party specifed in providerId, which we will attempt to match against our map of venues to URLs.
            """
            return self.GET(u'/venues/search', params)

        def trending(self, params):
            """ GET: https://api.foursquare.com/v2/venues/trending
            Returns a list of venues near the current location with the most people currently checked in.
                @ll : [required] Latitude and longitude of the user's location.
                @limit : Number of results to return, up to 50.
                @radius : Radius in meters, up to approximately 2000 meters.
            """
            return self.GET(u'/venues/trending', params)

        def herenow(self, VENUE_ID, params={}):
            """ GET: https://api.foursquare.com/v2/venues/VENUE_ID/herenow
            Provides a count of how many people are at a given venue.
            If the request is user authenticated, also returns a list of the users there, friends-first.
                @limit : Number of results to return, up to 500.
                @offset : Used to page through results.
                @afterTimestamp : Retrieve the first results to follow these seconds since epoch.
            """
            return self.GET(u'/venues/{VENUE_ID}/herenow'.format(VENUE_ID=VENUE_ID), params)

        def tips(self, VENUE_ID, params={}):
            """ GET: https://api.foursquare.com/v2/venues/VENUE_ID/tips
            Returns tips for a venue.
                @sort : One of recent or popular.
                @limit : Number of results to return, up to 500.
                @offset : Used to page through results.
            """
            return self.GET(u'/venues/{VENUE_ID}/tips'.format(VENUE_ID=VENUE_ID), params)

        def photos(self, VENUE_ID, params={}):
            """ GET: https://api.foursquare.com/v2/venues/VENUE_ID/photos
            Returns photos for a venue.
                @group : Pass checkin for photos added by friends on their recent checkins.
                         Pass venue for public photos added to the venue by anyone.
                         Use multi to fetch both.
                @limit : Number of results to return, up to 500.
                @offset : Used to page through results.
            """
            return self.GET(u'/venues/{VENUE_ID}/photos'.format(VENUE_ID=VENUE_ID), params)

        def links(self, VENUE_ID):
            """ GET: https://api.foursquare.com/v2/venues/VENUE_ID/links
            Returns URLs or identifiers from third parties that have been applied to this venue.
            """
            return self.GET(u'/venues/{VENUE_ID}/links'.format(VENUE_ID=VENUE_ID))



    class Checkins(_Endpoint):
        """Checkin specific endpoint"""
        def __call__(self, CHECKIN_ID, params={}):
            """ GET: https://api.foursquare.com/v2/checkins/CHECKIN_ID
            Get details of a checkin.
                @signature : When checkins are sent to public feeds such as Twitter, foursquare appends
                             a signature (s=XXXXXX) allowing users to bypass the friends-only access check on checkins.
            """
            return self.GET(u'/checkins/{CHECKIN_ID}'.format(CHECKIN_ID=CHECKIN_ID), params)

        def add(self, params):
            """ POST: https://api.foursquare.com/v2/checkins/add
            Allows you to check in to a place.
                @venueId: The venue where the user is checking in.
                           No venueid is needed if shouting or just providing a venue name.
                @venue: If are not shouting, but you don't have a venue ID or would rather prefer
                         a 'venueless' checkin, pass the venue name as a string using this parameter.
                @shout: A message about your check-in. The maximum length of this field is 140 characters.
                @broadcast: Who to broadcast this check-in to. Accepts a comma-delimited list of
                             values: private,public,facebook,twitter,followers
                @ll : Latitude and longitude of the user's location.
            """
            return self.POST(u'/checkins/add', params)

        def recent(self, params={}):
            """ GET: https://api.foursquare.com/v2/checkins/recent
            Returns a list of recent checkins from friends.
                @ll : Latitude and longitude of the user's location, so response can include distance.
                @limit : Number of results to return, up to 100.
                @afterTimestamp : Seconds after which to look for checkins, e.g. for looking for new checkins since the last fetch.
            """
            return self.GET(u'/checkins/recent', params)



    class Tips(_Endpoint):
        """Tips specific endpoint"""
        def __call__(self, TIP_ID):
            """ GET: https://api.foursquare.com/v2/tips/TIP_ID
            Gives details about a tip, including which users (especially friends) have marked the tip to-do or done.
            """
            return self.GET(u'/tips/{TIP_ID}'.format(TIP_ID=TIP_ID))

        def add(self, params):
            """ POST: https://api.foursquare.com/v2/tips/add
            Allows you to add a new tip at a venue. 
                @venueId: The venue where you want to add this tip.
                @text: The text of the tip, up to 200 characters.
                @url: A URL related to this tip.
                @broadcast: Whether to broadcast this tip. Send 'twitter' if you want to send to
                             twitter, 'facebook' if you want to send to facebook, or 'twitter,facebook'
                             if you want to send to both.
            """
            return self.POST(u'/tips/add', params)

        def search(self, params):
            """ GET: https://api.foursquare.com/v2/tips/search
            Returns a list of tips near the area specified.
                @ll : [required] Latitude and longitude of the user's location.
                @limit : Number of results to return, up to 500.
                @offset : Used to page through results.
                @filter : If set to friends, only show nearby tips from friends.
                @query : Only find tips matching the given term, cannot be used in conjunction with friends filter.
            """
            return self.GET(u'/tips/search', params)



    class Photos(_Endpoint):
        """Photo specific endpoint"""
        def __call__(self, PHOTO_ID):
            """ GET: https://api.foursquare.com/v2/photos/PHOTO_ID
            Get details of a photo.
            """
            return self.GET(u'/photos/{PHOTO_ID}'.format(PHOTO_ID=PHOTO_ID))



    class Settings(_Endpoint):
        """Setting specific endpoint"""
        def __call__(self):
            """ GET: https://api.foursquare.com/v2/settings/all
            Returns a setting for the acting user.
            """
            return self.GET(u'/settings/all')



    class Specials(_Endpoint):
        """Specials specific endpoint"""
        def __call__(self, SPECIAL_ID, params):
            """ GET: https://api.foursquare.com/v2/specials/SPECIAL_ID
            Gives details about a special, including text and whether it is unlocked for the current user.
                @venueId : [required] ID of a venue the special is running at
            """
            return self.GET(u'/specials/{SPECIAL_ID}'.format(SPECIAL_ID=SPECIAL_ID), params)

        def search(self, params):
            """ GET: https://api.foursquare.com/v2/specials/search
            Returns a list of specials near the current location.
                @ll : [required] Latitude and longitude to search near.
                @llAcc : Accuracy of latitude and longitude, in meters.
                @alt : Altitude of the user's location, in meters.
                @altAcc : Accuracy of the user's altitude, in meters.
                @limit : Number of results to return, up to 50.
            """
            return self.GET(u'/specials/search', params)
