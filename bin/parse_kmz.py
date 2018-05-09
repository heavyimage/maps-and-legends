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

        # because OF COURSE google maps kml stores things lon, lat not lat lon
        lon, lat, alt = unicode(placemark.Point.coordinates).strip().split("," )
        self.coords = "%s,%s" % (lat, lon)

    def __unicode__(self):
        return "(%s) %s (%s)" % (self.layer, self.name, self.description)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def bake(self):

        output_dir = os.path.join(os.getcwd(), "_waypoints")
        if not os.path.exists(output_dir):
            raise RuntimeError("Can't find _waypoints dir; re-run from jekyll "
                    "site root!")

        base = ''.join(ch.lower() for ch in self.name if ch.isalnum())
        filename = "%s.md" % base
        output_path = os.path.join(output_dir, filename)

        lines = [u'---\n',
                 u'title: "%s"\n' % self.name,
                 u'description: >-\n  %s\n' % self.description,
                 u'latlng: [%s]\n' % self.coords,
                 u'zoom: 12\n',
                 u'layer: %s\n' % self.layer,
                 u'---\n']
        with codecs.open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)


kmz = ZipFile(sys.argv[1], 'r')
doc = parser.parse(kmz.open('doc.kml', 'r')).getroot()
folders = doc.findall('.//{http://www.opengis.net/kml/2.2}Folder')


i = 0
for folder in folders:
    print folder.name
    for pm in folder.Placemark:
        i+=1
        place = Place(pm, folder.name)
        place.bake()
