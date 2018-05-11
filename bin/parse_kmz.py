import os
import sys
from zipfile import ZipFile
from pykml import parser
import codecs

class Place(object):
    def __init__(self, placemark, layer):
        self.name = unicode(placemark.name).strip()
        if hasattr(placemark, "description"):
            self.description = unicode(placemark.description).strip()
        else:
            self.description = ""

        # Reauthor layer names!
        layer = unicode(layer).lower().strip()
        if layer == unicode("random stuff worth seeing"):
            layer = "pois"
        elif layer == unicode("coffee shops"):
            layer = "coffee"
        elif layer == unicode("board game cafes"):
            layer = "boardgamecafes"
        self.layer = layer

        pair = self.placemark_to_coords(placemark)
        self.coords = [pair]

    def placemark_to_coords(self, placemark):
        # because OF COURSE google maps kml stores things lon, lat not lat lon
        lon, lat, alt = unicode(placemark.Point.coordinates).strip().split("," )
        pair = "%s,%s" % (lat, lon)
        return pair

    def add_coord(self, placemark):
        pair = self.placemark_to_coords(placemark)
        self.coords.append(pair)

    def __unicode__(self):
        return "(%s) %s (%s)" % (self.layer, self.name, self.description)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def get_output_path(self):
        output_dir = os.path.join(os.getcwd(), "_locations")
        if not os.path.exists(output_dir):
            raise RuntimeError("Can't find _locations dir; re-run from jekyll "
                    "site root!")

        base = ''.join(ch.lower() for ch in self.name
                if ch.isalnum() or ch == " ")
        base = base.replace(" ", "_")
        filename = "%s.md" % base
        return os.path.join(output_dir, filename)

    def bake(self):
        output_path = self.get_output_path()

        with codecs.open(output_path, "w", encoding="utf-8") as f:
            f.write(u'---\n')
            f.write(u'title: "%s"\n' % self.name)
            f.write(u'description: >-\n  %s\n' % self.description)
            f.write(u'latlng:\n')
            for coord in self.coords:
                f.write(u'  - %s\n' % coord)
            f.write(u'zoom: 12\n')
            f.write(u'layer: %s\n' % self.layer)
            f.write(u'---\n')


kmz = ZipFile(sys.argv[1], 'r')
doc = parser.parse(kmz.open('doc.kml', 'r')).getroot()
folders = doc.findall('.//{http://www.opengis.net/kml/2.2}Folder')

# Build places
places = []
for folder in folders:
    print folder.name
    for pm in folder.Placemark:
        place = Place(pm, folder.name)
        previous = next((p for p in places if p.get_output_path() == place.get_output_path()), None)
        if previous:
            previous.add_coord(pm)
        else:
            places.append(place)

# Check that there aren't any collisions
collisions = []
paths = [place.get_output_path() for place in places]
for place in places:
    my_path = place.get_output_path()
    if paths.count(my_path) > 1:
        collisions.append(place)

collisions = sorted(["%s (%s)" % (place.name, place.coords) for place in collisions])
if len(collisions):
    raise RuntimeError("Can't proceed -- collision between output files!  I probably should have a better naming approach...right?"
                       "\n\t%s" % ("\n\t".join(collisions)))

for place in places:
    place.bake()
