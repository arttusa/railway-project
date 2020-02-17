import config
from pymongo import MongoClient


def handle_arrival_update(train):
    print('arrival metodista:', train)

    client = MongoClient(config.MONGO_URL)
    mydb = client["stations"] 
    mycollection = mydb["Locations"] 

    mycollection.update_one(
        {'tpl': train['tpl'], 'trains.rid': train['rid'] }, 
        { "$set": {'trains.$.pta': train['new_pta']} }
    )
    print('valmis')

def handle_departure_update(train):
    print('departure metodista:', train)

    client = MongoClient(config.MONGO_URL)
    mydb = client["stations"] 
    mycollection = mydb["Locations"] 

    mycollection.update_one(
        {'tpl': train['tpl'], 'trains.rid': train['rid'] }, 
        { "$set": {'trains.$.ptd': train['new_ptd']} }
    )
    print('valmis')