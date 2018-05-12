import readline
import yaml
import requests
import pprint

def main():

    # load the project's config file
    with open("../_config.yml") as c:
        config = yaml.load(c)

    choice = "n"
    while choice != "y" and choice != "":
        text = raw_input("Enter the name of the location: ")
        #location = geolocator.geocode(text)
        response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=%s' % text)
        resp_json_payload = response.json()
        results = resp_json_payload['results']
        print "%s results found" % len(results)
        for result in results:
            print result['formatted_address']
            print
            print "  * %s" % "\n  * ".join([type_.title() for type_ in result['types']])
            print 
            for key, value in result['geometry']['location'].items():
                print "%s: %s" % (key, value)
            choice = raw_input("\nDoes this look correct? (Y/n)")

    print

    layer_id = ""
    while layer_id == 0:
        for i, layer in enumerate(config['layers'], 1):
            print i, layer['title']
        layer_id = raw_input("Chose a layer!")

    layer = config['layers'][int(layer_id)]
    print layer

if __name__ == "__main__":
    main()
