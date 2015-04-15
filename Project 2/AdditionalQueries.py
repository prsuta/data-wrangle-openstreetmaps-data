from pymongo import MongoClient
import pprint

#
# This file contains additional queries used to create different statistics about Frankfurt districts.
#

# gets the connection to a database with name db_name
def getdb(db_name):
    client = MongoClient('localhost:27017')
    return client[db_name]

# gets the 5 most numerous amenities of Frankfurt am Main
def get_top_amentites(db):
    agg = db.cities.aggregate([{"$match":{"amenity":{"$exists":1}}},
            {"$group": {"_id": {"Amenity":"$amenity"}, "count": {"$sum": 1}}},
            {"$project": {'_id':0, "Amenity":"$_id.Amenity", "Count":"$count"}},
            {"$sort": {"Count": -1}},
            {"$limit" : 5 }])
    pprint.pprint(agg)

# gets the top 3 dining districts of Frankfurt am Main with the most cafes and restaurants
def get_top_outing_district(db):
    agg = db.cities.aggregate([{"$match":{"amenity":{"$exists":1}, "address.city":{"$exists":1},
                                          "amenity":{"$in":["cafe","restaurant"]}}},
            {"$group":{"_id":{"District":"$address.city"}, "Total": {"$sum":1}}},
            {"$project":{"_id":0, "District":"$_id.District", "Count":"$Total"}},
            {"$sort":{"Count":-1}},
            {"$limit":3}])
    pprint.pprint(agg)

# gets the top 2 cuisines for a certain districts of Frankfurt am Main
def get_top_food(db, district):
    agg = db.cities.aggregate([{"$match":{"amenity":{"$exists":1}, "address.city":{"$exists":1},
                                          "cuisine":{"$exists":1}, "amenity":"restaurant",
                                          "address.city":district}},
            {"$group":{"_id":{"District":"$address.city", "Food":"$cuisine"}, "Total": {"$sum":1}}},
            {"$project":{"_id":0, "District":"$_id.District", "Food":"$_id.Food", "Count":"$Total"}},
            {"$sort":{"Count":-1}},
            {"$limit":2}])
    pprint.pprint(agg)

# gets the most family friendly 3 districts of Frankfurt am Main with the most schools
def get_kindergarten(db):
    agg = db.cities.aggregate([{"$match":{"amenity":{"$exists":1}, "address.city":{"$exists":1},
                                          "amenity":{"$in":["school"]}}},
            {"$group":{"_id":{"District":"$address.city", "Type":"$amenity"}, "Total": {"$sum":1}}},
            {"$project":{"_id":0, "District":"$_id.District", "TypeOfSchool":"$_id.Type", "Count":"$Total"}},
            {"$sort":{"Count":-1}},
            {"$limit":3}])
    pprint.pprint(agg)

# gets the top 3 bakeries covering most of Frankfurt am Main
def get_shops(db):
    agg = db.cities.aggregate( [{"$match":{"shop":{"$exists":1}, "shop":"bakery", "name":{"$exists":1}}},
                                {"$group":{"_id":{"District":"$address.city", "Name":{"$toLower": "$name"}}, "count":{"$sum":1}}},
                                {"$project": {'_id':0, "District":"$_id.District", "Name":"$_id.Name", "Count":"$count"}},
                                {"$sort":{"Count":-1}}, {"$limit":3}])
    pprint.pprint(agg)


if __name__ == "__main__":
    db = getdb('ffm')
    #get_top_amentites(db)
    #get_top_outing_district(db)
    #get_top_food(db, "Frankfurt am Main - Altstadt")
    #get_top_food(db, "Frankfurt am Main - Bornheim")
    #get_kindergarten(db)
    get_shops(db)