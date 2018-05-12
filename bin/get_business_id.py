import os
import json
import requests
import pickle
import pprint

VENUE_EXPLORE_URL = 'https://api.foursquare.com/v2/venues/explore'
VENUE_DETAILS_URL = 'https://api.foursquare.com/v2/venues/%s'
CACHE = "output.dat"
CACHE2 = "output2.dat"

params = dict(
  client_id='XYU3UGC54SLPDLBXECKIQRJNYPGUVGGAPY0QDYLATSHUHSDW',
  client_secret='VBLAR4GDMZCRIDZD4B4O05EFBCBXAAKWMMIXJNE32JFKSJPL',
  v='20180323',
  ll='40.774625,-73.958731',
  query='candle 79',
  limit=1
)
def explore_group(group):
    #pprint.pprint(group)
    for item in group['items']:
        print "Exact match:", item['flags']['exactMatch']
        print "Foursquare Id:", item['venue']['id']
        #print "Foursquare Venue Page:", item['venue']['venuePage']['id']
        print "Address:", " ".join(item['venue']['location']['formattedAddress'])
        print "Photos:", item['venue']['photos']
        print "Exact match:", item['flags']['exactMatch'] == True

        print "\n\n\n*** Details ***\n\n\n"

        url = VENUE_DETAILS_URL % item['venue']['id']
        if not os.path.exists(CACHE2):
            resp = requests.get(url=url, params=params)
            data = json.loads(resp.text)

            with open(CACHE2, "w") as f:
                pickle.dump(data, f)

        with open(CACHE2, "r") as f:
            data = pickle.load(f)
        #pprint.pprint(data)
        groups = data['response']['venue']['attributes']['groups']
        for group in groups:
            print group['name']
            #pprint.pprint(group)

        menus = [g for g in groups if g['name'] == "Menus"]

        print "\n\n\n\n"
        best_photo = data['response']['venue']['bestPhoto']
        print "Photo:", best_photo
        categories = data['response']['venue']['categories']
        print "Categories:", [cat['shortName'] for cat in categories]
        phone = data['response']['venue']['contact']['formattedPhone']
        print "Phone:", phone
        hours = data['response']['venue']['hours']['timeframes']
        print "Hours:", hours
        menu = data['response']['venue']['menu']['url']
        print "Menu URL", menu

        price = data['response']['venue']['price']
        print "Price:", price
        rating = data['response']['venue']['rating']
        rating_signals = data['response']['venue']['ratingSignals']
        print "Rating:", rating, "based on", rating_signals, "reviews"
        url = data['response']['venue']['url']
        print "URL", url

if not os.path.exists(CACHE):
    resp = requests.get(url=VENUE_EXPLORE_URL, params=params)
    data = json.loads(resp.text)

    with open(CACHE, "w") as f:
        pickle.dump(data, f)


with open(CACHE, "r") as f:
    data = pickle.load(f)

    groups = data['response']['groups']
    print len(groups), "group(s):"
    for group in groups:
        explore_group(group)
