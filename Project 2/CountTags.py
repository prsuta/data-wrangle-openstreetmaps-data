#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Your task is to use the iterative parsing to process the map file and
find out not only what tags are there, but also how many, to get the
feeling on how much of which data you can expect to have in the map.
The output should be a dictionary with the tag name as the key
and number of times this tag can be encountered in the map as value.

Note that your code will be tested with a different data file than the 'example.osm'
"""
import xml.etree.ElementTree as ET
import pprint

# counts number of occurrences of different xml elements
def count_tags(filename):
    tagDict = {}
    # loops through the xml file taking each element
    for evt, elem in ET.iterparse(filename):
        # if element visited before increase the count of occurrences
        if (tagDict.has_key(elem.tag)):
            cnt = tagDict[elem.tag]
            cnt += 1
            tagDict[elem.tag] = cnt
        # no element in dict, add it
        else:
            tagDict[elem.tag] = 1
    return tagDict

# loads a target osm file and counts the number of element occurrences
def test():

    tags = count_tags('frankfurt.osm')
    pprint.pprint(tags)

if __name__ == "__main__":
    test()