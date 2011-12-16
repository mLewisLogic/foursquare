# foursquare

Python wrapper for the [foursquare v2 API](http://developer.foursquare.com/docs/).

Philosophy:

* Map foursquare's endpoints one-to-one
* Clean, simple, Pythonic calls
* Full coverage of Core API

Features:

* Automatic retries
* Useful exception classes
* Full test coverage (except the OAuth dance)


## Usage

### Authentication
The OAuth2 dance is untested. The functionality of this package is for once you have a user token (or wish to perform userless actions). Follow the guide [here](https://developer.foursquare.com/overview/auth) to get the user's access token.


### Instantiating a client
#### [Userless Access](https://developer.foursquare.com/overview/auth)
    client = foursquare.Foursquare(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')

#### [Authenticated User Access](https://developer.foursquare.com/overview/auth)
    client = foursquare.Foursquare(access_token='USER_ACCESS_TOKEN')


#### [Specifing a specific API version](https://developer.foursquare.com/overview/versioning)
    client = foursquare.Foursquare(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET', version='20111215')
    client = foursquare.Foursquare(access_token='USER_ACCESS_TOKEN', version='20111215')


### Examples

#### Users
##### [Getting your own user object](https://developer.foursquare.com/docs/users/users)
    client.users()
##### [Getting another user](https://developer.foursquare.com/docs/users/users)
    client.users(1183247)
##### [Get your checkins](https://developer.foursquare.com/docs/users/checkins)
    client.users.checkins()
##### [Get your most recent checkin](https://developer.foursquare.com/docs/users/checkins)
    client.users.checkins(params={'limit': 1})
##### Get *all* of your friends' checkins (not a native 4sq call)
    client.users.all_checkins(1183247)
##### [Approve a friend's friend request](https://developer.foursquare.com/docs/users/approve)
    client.users.approve(1183247)

#### Venues
##### [Get details about a venue](https://developer.foursquare.com/docs/venues/venues)
    client.venues('40a55d80f964a52020f31ee3')
##### [Search for a coffee place](https://developer.foursquare.com/docs/venues/search)
    client.venues.search(params={'query': 'coffee'})
##### [Mark a venue to-do](https://developer.foursquare.com/docs/venues/marktodo)
    client.venues.marktodo('40a55d80f964a52020f31ee3')

#### Checkins
##### [Get recent checkins for yourself](https://developer.foursquare.com/docs/checkins/recent)
    client.checkins.recent()
##### [Get recent checkins for a friend](https://developer.foursquare.com/docs/checkins/recent)
    client.checkins.recent(1183247)

#### Tips
##### [Get a specific tip](https://developer.foursquare.com/docs/tips/tips)
    client.tips('4b5e662a70c603bba7d790b4')
##### [Search for a tip](https://developer.foursquare.com/docs/tips/search)
    client.tips.search(params={'query': 'donuts'})


### Full endpoint list
Note: endpoint methods map one-to-one with foursquare's endpoints

    users()
    users.leaderboard()
    users.requests()
    users.search()
    users.badges()
    users.checkins()
    users.all_checkins() [*not native*]
    users.friends()
    users.lists()
    users.mayorships()
    users.photos()
    users.venuehistory()
    users.approve()
    users.deny()
    users.request()
    users.setpings()
    users.unfriend()
    users.update()
    
    venues()
    venues.add()
    venues.categories()
    venues.explore()
    venues.search()
    venues.trending()
    venues.events()
    venues.herenow()
    venues.listed()
    venues.photos()
    venues.similar()
    venues.tips()
    venues.flag()
    venues.marktodo()
    venues.proposeedit()
    
    checkins()
    checkins.add()
    checkins.recent()
    checkins.addcomment()
    checkins.deletecomment()
    
    tips()
    tips.add()
    tips.search()
    tips.done()
    tips.listed()
    tips.markdone()
    tips.marktodo()
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
    specials.flag()
    
    events()
    events.categories()
    events.search()

## Improvements
What else would you like this library to do? Let me know. Feel free to send pull requests for any improvements you make.

### Todo
* Get OAuth dance working (with unit tests)
* Test coverage for write methods
* Bring in new endpoints as they emerge
* Merchant-specific endpoints (someday)

## License
MIT License. See LICENSE
Copyright (c) 2011 Mike Lewis
