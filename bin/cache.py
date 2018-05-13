import os
import sys
import datetime
import json
import cPickle as pickle
import time
import requests
import threading
import urllib
import Queue
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.routing import FloatConverter as BaseFloatConverter

from secret import *

VENUE_EXPLORE_URL = 'https://api.foursquare.com/v2/venues/search'
VENUE_DETAILS_URL = 'https://api.foursquare.com/v2/venues/%s'

DISK_CACHE = "cache.p"
THRESHOLD = 60*60*24*30     # Number of seconds cache stays valid for; 1 month
EXPIRY_KEY = "JS_FETCH_TIME"

VERSION = 20180511

DUMMY_IMAGE = "<img width='300' height='300' src='/assets/images/unknown.png'>" 


# Define app
app = Flask(__name__)

# Flask hack #1 -- CORS
CORS(app)   # TODO: what is this actually doing?

# Flask hack #2 -- Default Float Convert doesn't handle negative numbers!
# Must be done before routes are registered
class FloatConverter(BaseFloatConverter):
    regex = r'-?\d+(\.\d+)?'
app.url_map.converters['float'] = FloatConverter


# Set up multithreading stuff
fetching = threading.Condition()
fetching_queue = Queue.Queue()

# Ze all important memory cache!
cache = {}

@app.route('/')
def api_root():
    return 'Welcome'

@app.route('/q=<query>&ll=<float:lat>,<float:lng>')
def get_details(query, lat, lng):

    # convert lat, lng into a string(key) of 1 meter resolution
    # https://en.wikipedia.org/wiki/Decimal_degrees; down to ~1 meter
    key = "%.5f,%.5f" % (lat, lng)
    print "Request for '%s' @ %s" % (query, key)

    # * get json object from cache @ key
    details = get_details_from_cache(query, key)

    # convert into html for text, html for the image area
    html, img = get_metadata_from_details(details)

    # * serve back via return
    return json.dumps({'html': html, 'img': img})

def get_details_from_cache(query, key):

    # Define inner function for sending a query/key to the fetcher thread
    # We use this function twice in get_details_from_cache so #DRY
    def update_cache(query, key):
        with fetching:
            fetching_queue.put((query, key))
            while True:             # TODO: do I need this?
                fetching.wait()
                if key in cache:
                    break

    # * check if key exists in cache
    if key not in cache:
        print "\tCache MISS for '%s'" % key
        update_cache(query, key)

    data = cache[key]

    # Check for expiration; if it's over some threshold since this
    # info was fetched, we need to update our records!
    delta = datetime.datetime.now() - data[EXPIRY_KEY]
    print "Delta", delta.total_seconds()
    if delta.total_seconds() > THRESHOLD:
        print "\tCache EXPIRED (miss) for '%s'" % key
        update_cache(query, key)
    else:
        print "\tCache HIT for '%s'" % key

    return data

def process():
    while True:
        query, key = fetching_queue.get()
        if key in cache:
            fetching.notify_all()
            continue

        # fetch BUSINESS Id (api call #1)
        business_id = business_search(key, query)

        # If that business couldn't be found in the remote database...
        if business_id == None:
            print "\t\tNo business ID found for '%s' @ (%s)" % (query, key)
            data = {}

        else:
            # get details (api call #2)
            data = business_details(business_id)

            # Prune unused gigantic keys:
            venue = data['response']['venue']
            for unused_key in ["location", "likes", "hours", "listed", "tips",
                        "photos", "popular", "page"]:
                if unused_key in venue:
                    del venue[unused_key]

        # Add the fetch time for cache invalidation
        data[EXPIRY_KEY] = datetime.datetime.now()

        # store business details json in cache @ key
        with fetching:
            cache[key] = data
            fetching.notify_all()

        before = time.time()
        with open(DISK_CACHE, "w") as f:
            pickle.dump(cache, f)

def business_search(key, query):
    lat, lng = key.split(",")

    # Do the business search
    params = dict(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        v=VERSION,
        ll='%s,%s' % (lat, lng),
        query=query,
        radius=100,
        limit=1
    )

    try:
        resp = requests.get(url=VENUE_EXPLORE_URL, params=params)
        data = json.loads(resp.text)
    except ConnectionError as cne:
        print "Business Details: Connection error: %s" % cne
        return None

    # If we ddn't find anything, return None
    if len(data['response']['venues']) == 0:
        return None

    # Otherwise, fetch the venue
    venue = data['response']['venues'][0] # limit 1

    # Could name be improved?
    name = venue['name']
    if name != urllib.unquote_plus(query):
        print "\t\tPossibly better name for %s is %s" % (query, name)

    # This is the droids we're looking for:
    id_ = venue['id']
    print "\t\t%s --> %s" % (query, id_)

    return id_

def business_details(business_id):
    # Do the business search
    params = dict(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        v=VERSION
    )

    url = VENUE_DETAILS_URL % business_id

    try:
        resp = requests.get(url=url, params=params)
        data = json.loads(resp.text)
    except ConnectionError as cne:
        print "Business Details: Connection error: %s" % cne
        return {}

    print "\t\t%s --> %s" % (business_id, "<JSON>")
    return data

def get_metadata_from_details(details):

    # If there's only one key it's the JS_FETCH_TIME so there's no content...
    if len(details) == 1:
        return "<p>No extra data available!<p>", DUMMY_IMAGE

    # Cache some inner dicts that are bound to be there
    response = details['response']
    venue = response['venue']

    html = ""

    # Description
    description = venue.get('description', {})
    if description:
        html += "<strong>Official Description:</strong> %s <br>" % (description)

    # Categories:
    if venue.get('categories'):
        html += "<strong>Categories:</strong> %s<br>" % (
                ", ".join([cat['shortName'] for cat in venue['categories']]))

    # Price
    price = venue.get('price', {})
    if price:
        html += "<strong>Price:</strong> %s (%s) <br>" % (
                int(price['tier']) * price['currency'], price['message'])

    # Some of these things are grouped...not sure why?
    groups = venue['attributes']['groups']
    for group in groups:
        name = group['name']

        # Serves (brunch?  Lunch? etc)
        if name == "Menus":
            options = [item['displayValue'] for item in group['items']]
            html += "<strong>Serves:</strong> %s<br>" % (", ".join(options))

        # Take out?
        elif name == "Dining Options":
            options = [item['displayValue'] for item in group['items']]
            html += "<strong>Options:</strong> %s<br>" % (", ".join(options))

    # web contact
    url = venue.get('url', {})
    twitter = venue.get('contact', {}).get('twitter', {})
    contact = []
    if url:
        contact.append("<a href='%s'>%s</a>" % (url, url))
    if twitter:
        contact.append("<a href='http://www.twitter.com/%s'>@%s</a>" % (
                twitter, twitter))

    html += " &#x2F; ".join(contact) # forward slash!
    html += "<br>"

    # Photos:
    best_photo = venue.get('bestPhoto', None)
    photo_html = ""
    if best_photo:
        photo_path = "%s%s%s" % (
                best_photo['prefix'], "300x300", best_photo['suffix'])
        photo_html = "<img src='%s'><br>" % (photo_path)
    else:
        photo_html = DUMMY_IMAGE

    return html, photo_html

if __name__ == '__main__':

    # set up thread to perform bg fetches
    processor = threading.Thread(name='processor', target=process)
    processor.setDaemon(True)
    processor.start()

    # Read in cache if extant
    if os.path.exists(DISK_CACHE):
        with open(DISK_CACHE) as f:
            cache = pickle.load(f)
        print "\n<< Loaded %s entries from disk! >>\n" % len(cache)
    else:
        print "\n<< No Cache Found! >>\n"

    # Lets do this!
    app.run()


