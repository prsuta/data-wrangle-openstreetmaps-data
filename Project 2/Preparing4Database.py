# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json

# regex expressions for cleaning
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# tags with creation information that we want
created = ["version", "changeset", "timestamp", "user", "uid"]

# single name for Frankfurt and its districts we want to use for all synonyms
ffm_expected = ["Frankfurt am Main", "Frankfurt am Main - Nied", "Frankfurt am Main - Hausen",
                "Frankfurt am Main - Ostend", "Frankfurt am Main - Griesheim", u"Frankfurt am Main - Rödelheim"]

# mapping for city and district names that we want to transform
ffm_mapping = {"Frankfurt/M": "Frankfurt am Main",
               "Frankfurt/Main": "Frankfurt am Main",
               "Frankfurt": "Frankfurt am Main",
               "Frankfurt a. M.": "Frankfurt am Main",
               "Frankfurt-Hausen": "Frankfurt am Main - Hausen",
               "Frankfurt-Ostend": "Frankfurt am Main - Ostend",
               "Frankfurt-Griesheim": "Frankfurt am Main - Griesheim",
               u"Frankfurt-Rödelheim": u"Frankfurt am Main - Rödelheim",
               u"Rödelheim": u"Frankfurt am Main - Rödelheim"}

# post codes that are not assigned to Frankfurt districts and that we want to remove from the final data set
plz_not_expected = ["63477", "63069", "65929", "65760", "63067", "63065", "63075", "65933", "63073", "61449",
                    "65824", "63071"]

# correct mapping between post codes and district names
plz_ffm_mapping = {"60306": "Frankfurt am Main - Opernturm",
                   "60310": "Frankfurt am Main - Innenstadt",
                   "60311": "Frankfurt am Main - Altstadt",
                   "60313": "Frankfurt am Main - Altstadt",
                   "60314": "Frankfurt am Main - Fechenheim",
                   "60316": "Frankfurt am Main - Nordend-Ost",
                   "60318": "Frankfurt am Main - Nordend-West",
                   "60320": "Frankfurt am Main - Westend-Nord",
                   "60322": "Frankfurt am Main - Dornbusch",
                   "60323": "Frankfurt am Main - Westend-Süd",
                   "60325": "Frankfurt am Main - Bockenheim",
                   "60326": "Frankfurt am Main - Griesheim",
                   "60327": "Frankfurt am Main - Gutleutviertel",
                   "60329": "Frankfurt am Main - Bahnhofsviertel",
                   "60385": "Frankfurt am Main - Bornheim",
                   "60386": "Frankfurt am Main - Riederwald",
                   "60388": "Frankfurt am Main - Bergen-Enkheim",
                   "60389": "Frankfurt am Main - Seckbach",
                   "60431": "Frankfurt am Main - Ginnheim",
                   "60433": "Frankfurt am Main - Frankfurter Berg",
                   "60435": "Frankfurt am Main - Berkersheim",
                   "60439": "Frankfurt am Main - Heddernheim",
                   "60486": "Frankfurt am Main - Rödelheim",
                   "60487": "Frankfurt am Main - Hausen",
                   "60488": "Frankfurt am Main - Praunheim",
                   "60489": "Frankfurt am Main - Rödelheim",
                   "60528": "Frankfurt am Main - Niederrad",
                   "60529": "Frankfurt am Main - Schwanheim",
                   "60594": "Frankfurt am Main - Sachsenhausen-Nord",
                   "60596": "Frankfurt am Main - Sachsenhausen-Nord",
                   "60598": "Frankfurt am Main - Sachsenhausen-Süd",
                   "60599": "Frankfurt am Main - Oberrad",
                   "65934": "Frankfurt am Main - Nied",
                   "65936": "Frankfurt am Main - Sossenheim",
                   "60308": "Frankfurt am Main - Innenstadt"}

# updates the city name based on the mapping
# example1: Frankfurt/M -> Frankfurt am Main
# example2: Frankfurt-Hausen -> Frankfurt am Main - Hausen
def update_city_name(name, mapping):
    better_name = name
    if mapping.has_key(name):
        better_name = mapping[name]
    return better_name


def shape_element(element):

    # dictionary that we use to generate json for node and its tags
    node = {}

    if element.tag == "node" or element.tag == "way":

        # loop through the node attributes
        # example: <node id="279852883" lat="50.1262944" lon="8.7077310" version="11" timestamp="2014-05-03T09:25:37Z"
        #           changeset="22100412" uid="1749482" user="Eljot8472">
        for key in element.attrib.keys():

            node["type"] = element.tag
            val = element.attrib[key]

            # group "version", "changeset", "timestamp", "user", "uid" into the "created" sub dictionary
            if key in created:

                if "created" not in node.keys():
                    node["created"] = {}
                node["created"][key] = val

            # group "lon", "lat" into the "pos" tuple
            elif key == "lat" or key == "lon":

                if "pos" not in node.keys():
                    node["pos"] = [0.0, 0.0]
                old_pos = node["pos"]
                if key == "lat":
                    new_pos = [float(val), old_pos[1]]
                else:
                    new_pos = [old_pos[0], float(val)]
                node["pos"] = new_pos

            # add other attributes as separate keys
            else:
                node[key] = val

            # loop through the tag elements of a node
            # example: <node...>
            #           <tag k="name" v="Eifler"/>
            #           <tag k="shop" v="bakery"/>
            #           <tag k="wheelchair" v="limited"/>
            #          </node>
            for tag in element.iter("tag"):

                tag_key = tag.attrib['k']
                tag_val = tag.attrib['v']

                # skip tags that have problematic chars
                if problem_chars.match(tag_key):
                    continue

                # group "version", "changeset", "timestamp", "user", "uid" into the "address" sub dictionary
                elif tag_key.startswith("addr:"):

                    if "address" not in node.keys():
                        node["address"] = {}
                    # extract the sub-keys for "address" sub-dictionary
                    # Example: <tag k="addr:city" v="Frankfurt"/> -> addr_key = "city"
                    addr_key = tag_key[len("addr:"):]
                    # skip unallowed address
                    if lower_colon.match(addr_key):
                        continue
                    else:
                        # extra cleaning for city names
                        if addr_key == "city":
                            tag_val = update_city_name(tag_val, ffm_mapping)
                            # do not include nodes of cities other than Frankfurt
                            if tag_val not in ffm_expected:
                                return None
                        # do not include nodes of districts other than those in Frankfurt
                        elif addr_key == "postcode":
                            if tag_val in plz_not_expected:
                                return None
                        node["address"][addr_key] = tag_val
                # use international format for phone numbers
                elif tag_key.startswith("phone"):
                    phn = tag_val
                    # remove special signs and empty spaces
                    phn = phn.translate(None, '!@#$/-*()')
                    phn = phn.translate(None, ' ')
                    # add german country code
                    if phn.startswith("069") or phn.startswith("061") or phn.startswith("017") or phn.startswith("051"):
                        phn = '+49' + phn[1:]
                    elif phn.startswith("49"):
                        phn = '+' + phn
                    elif phn.startswith("0049"):
                        phn = '+' + phn[3:]
                    if len(phn) > 4:
                        node[tag_key] =phn
                elif lower_colon.match(tag_key):
                    node[tag_key] = tag_val
                else:
                    node[tag_key] = tag_val

        for tag in element.iter("nd"):
            if "node_refs" not in node.keys():
                node["node_refs"] = []
            node_refs = node["node_refs"]
            node_refs.append(tag.attrib["ref"])
            node["node_refs"] = node_refs

        # assign postcode to proper district
        if node.has_key("address"):
            if node["address"].has_key("postcode"):
                node["address"]["city"] = plz_ffm_mapping[node["address"]["postcode"]]
            else:
                node["address"]["postcode"] = "60311"

        return node
    else:
        return None


def process_map(file_in, pretty=False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w", encoding="utf-8") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                # data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2) + "\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data


def test():
    # NOTE: if you are running this code on your computer, with a larger dataset,
    # call the process_map procedure with pretty=False. The pretty=True option adds
    # additional spaces to the output, making it significantly larger.
    data = process_map('frankfurt.osm', False)


if __name__ == "__main__":
    test()
