import boto3
import os
import zlib
import gzip
import shutil
import json
from pymongo import MongoClient
from pprint import pprint
import xml.etree.ElementTree as ET
import config

def parseLocationRef():
    date = "20200217"
    for file in os.listdir("./PPTimetable"):
        if date in file and "ref" in file and "v3" in file and file.endswith(".xml"): # find the right file
            unzippedfilepath = "./PPTimetable/"+file

    tree = ET.parse(unzippedfilepath)
    root = tree.getroot()
    allData = []
    for location in root.findall('./'+root[0].tag):
        #print(location.attrib['locname'])
        data = location.attrib
        allData.append(data)
    
    print(allData)
    
    #inserting to database
    client = MongoClient(config.MONGO_URL)
    mydb = client["stations"] 
    mycollection = mydb["Locations"] #make a collection 
    mycollection.insert_many(allData)
    

def parseJourneys():
    # let's use as an example Liverpool Lime Street tpl="LVRPLSH"
    date = "20200217"
    stationTPL = 'LVRPLSH'
    for file in os.listdir("./PPTimetable"):
        if date in file and "v8" in file and file.endswith(".xml"): # find the right file
            unzippedfilepath = "./PPTimetable/"+file
    
    tree = ET.parse(unzippedfilepath)
    root = tree.getroot()
    allTrains = []
    x = 0
    for journey in root.findall('./'+root[0].tag):
        train = {}
        origin = ""
        destination = ""

        #print(journey)
        #print(location.attrib['locname'])
        for info in journey:
            if info.tag.endswith('OR'):
                origin = info.attrib['tpl']
                #print(info.tag)
            if info.tag.endswith('DT'):
                destination = info.attrib['tpl']
                #print(info.tag)
       
            # here handle cancelled trains
            if info.text != None:
                if "cancelReason" in info.tag:
                    #print('cancelReason', info.text)
                    break
            
            if info.attrib['tpl'] == stationTPL: # get every train that goes from or to the specific station
                train['rid'] = journey.attrib['rid']
                x += 1
                train['uid'] = journey.attrib['uid']
                train['trainId'] = journey.attrib['trainId']
                train['ssd'] = journey.attrib['ssd']
                train['toc'] = journey.attrib['toc']
                if 'pta' in info.attrib:
                    train['pta'] = info.attrib['pta'] # Public Scheduled Time of Arrival
                if 'ptd' in info.attrib:
                    train['ptd'] = info.attrib['ptd'] # Public Scheduled Time of Departure
                if 'wta' in info.attrib: 
                    train['wta'] = info.attrib['wta'] # Working Scheduled Time of Arrival
                if 'wtd' in info.attrib:
                    train['wtd'] = info.attrib['wtd'] # Working Scheduled Time of Departure
                if 'wtp' in info.attrib: 
                    train['wtp'] = info.attrib['wtp'] # Working Scheduled Time of Passing
                    
                    
        if train.get('rid') == journey.attrib['rid']:
            train['origin'] = origin
            train['destination'] = destination # here because it is always the last child of the journey object
            allTrains.append(train) # inserting finally when destination has got
 
    # updating database with journeys information
    json_data = json.dumps(allTrains, indent=2)
    print(json_data)
    
    client = MongoClient(config.MONGO_URL)
    mydb = client["stations"] 
    mycollection = mydb["Locations"] 
    mycollection.update_one({'tpl' : stationTPL}, 
        {'$set' : {"trains" : allTrains}})
    
    print("finished")
    


def fetchAWS ():
    # amazon credentials 
    resource = boto3.resource(
        's3',
        region_name='eu-west-1',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    )

    # fetching from the s3 bucket
    bucket = resource.Bucket('darwin.xmltimetable')

    for s3_object in bucket.objects.filter(Prefix="PPTimetable"):

        dirpath='./'+os.sep.join(s3_object.key.split(os.sep)[:-1])
        
        if not os.path.exists(dirpath): # make dir if not already made
            os.makedirs(dirpath)

        if not os.path.exists(s3_object.key): # check duplicates
            bucket.download_file(s3_object.key, './'+s3_object.key)
            print('DOWNLOADING',s3_object.key, 'TO', dirpath)




    directory = os.fsencode(dirpath)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        unzippedfilepath = dirpath+'/'+filename[:-3]
        if filename.endswith(".xml.gz") and not os.path.exists(unzippedfilepath): # check if already unzipped
            with gzip.open(dirpath+'/'+filename, 'rb') as f_in:
                with open(unzippedfilepath, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    #parseData(unzippedfilepath) # problems


fetchAWS()
parseLocationRef()
parseJourneys()
