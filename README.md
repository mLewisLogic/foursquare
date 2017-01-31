# foursquare

Python wrapper for the [foursquare API](http://developer.foursquare.com/docs/).

Philosophy:

* Map foursquare's endpoints one-to-one
* Clean, simple, Pythonic calls
* Only handle raw data, you define your own models

Features:

* Python 2+3 compatibility (via [@youngrok](https://github.com/youngrok))
* OAuth dance
* Automatic retries
* Full endpoint coverage (non-merchant)
* Full test coverage
* Useful exception classes
* Multi support (via [@benneic](https://github.com/benneic))

Dependencies:

* requests

## Installation

    pip install foursquare

or

    easy_install foursquare

Depending upon your system and virtualenv settings, these may require sudo permissions.

[PyPi page](https://pypi.python.org/pypi/foursquare)

## Usage

### Authentication

    # Construct the client object
    client = foursquare.Foursquare(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET', redirect_uri='http://fondu.com/oauth/authorize')

    # Build the authorization url for your app
    auth_uri = client.oauth.auth_url()

Redirect your user to the address *auth_uri* and let them authorize your app. They will then be redirected to your *redirect_uri*, with a query paramater of code=XX_CODE_RETURNED_IN_REDIRECT_XX. In your webserver, parse out the *code* value, and use it to call client.oauth.get_token()

    # Interrogate foursquare's servers to get the user's access_token
    access_token = client.oauth.get_token('XX_CODE_RETURNED_IN_REDIRECT_XX')

    # Apply the returned access token to the client
    client.set_access_token(access_token)

    # Get the user's data
    user = client.users()

### Instantiating a client
#### [Userless Access](https://developer.foursquare.com/overview/auth)
    client = foursquare.Foursquare(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')

#### [Authenticated User Access](https://developer.foursquare.com/overview/auth) (when you already have a user's access_token)
    client = foursquare.Foursquare(access_token='USER_ACCESS_TOKEN')


#### [Specifying a specific API version](https://developer.foursquare.com/overview/versioning)
    client = foursquare.Foursquare(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET', version='20111215')
or

    client = foursquare.Foursquare(access_token='USER_ACCESS_TOKEN', version='20111215')


### Examples

#### Users
##### [Getting your own user object](https://developer.foursquare.com/docs/users/users)
    client.users()
##### [Getting another user](https://developer.foursquare.com/docs/users/users)
    client.users('1183247')
##### [Get your checkins](https://developer.foursquare.com/docs/users/checkins)
    client.users.checkins()
##### [Get your most recent checkin](https://developer.foursquare.com/docs/users/checkins)
    client.users.checkins(params={'limit': 1})
##### Get *all* of your checkins (not a native 4sq call)
    client.users.all_checkins()
##### [Approve a friend's friend request](https://developer.foursquare.com/docs/users/approve)
    client.users.approve('1183247')

#### Venues
##### [Get details about a venue](https://developer.foursquare.com/docs/venues/venues)
    client.venues('40a55d80f964a52020f31ee3')
##### [Search for a coffee place](https://developer.foursquare.com/docs/venues/search)
    client.venues.search(params={'query': 'coffee'})
##### [Edit venue details](https://developer.foursquare.com/docs/venues/edit)
    client.venues.edit('40a55d80f964a52020f31ee3', params={'description': 'Best restaurant on the city'})

#### Checkins
##### [Returns a list of recent checkins from friends](https://developer.foursquare.com/docs/checkins/recent)
    client.checkins.recent()

#### Tips
##### [Get a specific tip](https://developer.foursquare.com/docs/tips/tips)
    client.tips('53deb1f6498e0d374af17ca7')
##### [Search for a tip](https://developer.foursquare.com/docs/tips/search)
    client.tips.search(params={'query': 'donuts'})


### Full endpoint list
Note: endpoint methods map one-to-one with foursquare's endpoints

    users()
    users.search()
    users.requests()
    users.checkins()
    users.all_checkins() [*not a native endpoint*]
    users.friends()
    users.lists()
    users.mayorships()
    users.photos()
    users.tips()
    users.venuehistory()
    users.venuelikes()
    users.approve()
    users.deny()
    users.setpings()
    users.unfriend()
    users.update()

    venues()
    venues.add()
    venues.categories()
    venues.explore()
    venues.managed()
    venues.search()
    venues.suggestcompletion()
    venues.trending()
    venues.events()
    venues.herenow()
    venues.links()
    venues.listed()
    venues.menu()
    venues.nextvenues()
    venues.photos()
    venues.similar()
    venues.stats()
    venues.tips()
    venues.nextvenues()
    venues.likes()
    venues.hours()
    venues.edit()
    venues.flag()
    venues.proposeedit()
    venues.setrole()

    checkins()
    checkins.add()
    checkins.recent()
    checkins.addcomment()
    checkins.addpost()
    checkins.deletecomment()

    tips()
    tips.add()
    tips.listed()
    tips.unmark()

    lists()
    lists.add()
    lists.followers()
    lists.suggestphoto()
    lists.suggesttip()
    lists.suggestvenues()
    lists.additem()
    lists.deleteitem()
    lists.follow()
    lists.moveitem()
    lists.share()
    lists.unfollow()
    lists.update()
    lists.updateitem()

    photos()
    photos.add()

    settings()
    settings.all()
    settings.set()

    specials()
    specials.search()
    specials.add()
    specials.flag()

    events()
    events.categories()
    events.search()

    pages()
    pages.venues()

    multi()


### Testing
In order to run the tests:
* Copy `foursquare/tests/_creds.example.py` to `foursquare/tests/_creds.py`
* Fill in your personal credentials to run the tests (`_creds.py` is in .gitignore)
* Run `nosetests`


## Improvements
Feel free to send pull requests for any improvements you make.

### TODO
* Bring in new endpoints as they emerge
* Test coverage for write methods


## Code status
* [![Build Status](https://travis-ci.org/mLewisLogic/foursquare.png?branch=master)](https://travis-ci.org/mLewisLogic/foursquare)

## License
MIT License. See LICENSE
Copyright (c) 2016 Mike Lewis
