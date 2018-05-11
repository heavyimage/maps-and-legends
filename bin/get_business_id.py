import os
import json
import requests
import pickle
import pprint

URL = 'https://api.foursquare.com/v2/venues/explore'
CACHE = "output.dat"

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
        print "Categories:", [cat['shortName'] for cat in item['venue']['categories']]
        print "Foursquare Id:", item['venue']['id']
        print "Foursquare Venue Page:", item['venue']['venuePage']['id']
        print "Address:", " ".join(item['venue']['location']['formattedAddress'])
        print "Photos:", item['venue']['photos']
        print "Exact match:", item['flags']['exactMatch'] == True


if not os.path.exists(CACHE):
    resp = requests.get(url=URL, params=params)
    data = json.loads(resp.text)

    with open(CACHE, "w") as f:
        pickle.dump(data, f)


with open(CACHE, "r") as f:
    data = pickle.load(f)

    groups = data['response']['groups']
    print len(groups), "group(s):"
    for group in groups:
        explore_group(group)
