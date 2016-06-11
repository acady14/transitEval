__author__ = 'acady'

import googlemaps
import json
import time
import csv
import math
import numpy as np
import datetime as dt
import pickle
import random
from RouteClass import route
from GmapsConnection import *
from geometry import *


query_name=str(dt.datetime.now().year)
query_name+=str(dt.datetime.now().month)
query_name+=str(dt.datetime.now().day)
query_name+=("_")
query_name+=(str(dt.datetime.now().hour))
query_name+=(str(dt.datetime.now().minute))
print(query_name)


########################################################################################################################
#################################////////////PARAMETER ENTRY\\\\\\\\\\\\\\##############################################
########################################################################################################################
# first, we need to read in our API key.  If you need an API key, they are available from Google for free up to 2500
# queries per day
with open('transitEvalApiKey.txt','r') as f:
    apikey=f.read()



modeList=['transit']#,'bicycling']

#Time to use for current pull...COMPLETED TIMES:
timesList=(dt.datetime(2016,6,16,7),)











# Other data that is useful for the program to run...
#Polygon #2:  this polygon encompasses 3 miles north of Expo line stations and 4 miles south
polygon=[(34.036763,-118.534884),
             (34.057280,-118.500412),
             (34.079303,-118.440661),
             (34.067740,-118.403639),
             (34.029623,-118.388831),
             (33.967029,-118.394050),
             (33.965821,-118.456077)
           ]

#there was an issue with roads changing, especially in downtown santa monica!
stationLocsll={"Downtown Santa Monica":(34.013666,-118.490970),
            "17th St-SMC":(34.023648,-118.479664),
            "26th-Bergamont Station":(34.027691,-118.468382),
            "Expo and Bundy":(34.031800,-118.453422),
            "Expo and Sepulveda":(34.035371,-118.434213),
            "Westwood and Rancho Park":(34.036517,-118.425091),
            "Palms Station":(34.029089,-118.403802),
            "Downtown Culver City":(34.027854,-118.388894),
            "La Cienega and Jefferson":(34.026359,-118.372171)
            }
stationLocsadd={"Downtown Santa Monica":'Downtown Santa Monica, 402 Colorado Ave, Santa Monica, CA 90401',
            "17th St-SMC":'17th St/SMC Station, 1610 Colorado Avenue, Santa Monica, CA 90404',
            "26th-Bergamont Station":'Bergamot Station, 2525 Michigan Avenue, Santa Monica, CA 90404',
            "Expo and Bundy":'Expo/Bundy Station, Exposition Corridor Bike Path, Los Angeles, CA 90064',
            "Expo and Sepulveda":'Expo/Sepulveda Station - Expo Metro Line, 11295 Exposition Boulevard, Los Angeles, CA 90064',
            "Westwood and Rancho Park":'Westwood/Rancho Park LA Metro Expo Line station, 2600 Westwood Boulevard, Los Angeles, CA 90064',
            "Palms Station":'Palms Station, 10021 National Boulevard, Los Angeles, CA 90034',
            "Downtown Culver City":'Culver City, 8817 Washington Boulevard, Culver City, CA 90232',
            "La Cienega and Jefferson":'La Cienega / Jefferson Station'
            }

directionList=['to_station','from_station']

header_row=[ 'driveFactor','origin id','route id','originAddress','direction','originLoc lat','originLoc lng','endAddress',
            'end lat','end lng','totDist', 'totTime', 'railStation', 'mode','time of day','exact time','numLines',
             'walkTime', 'walkDist','busTime','busDist','agencies',
            'fare','waitTime','1_stopName','1_stopLat','1_stopLng','1_line','2_stopName','2_stopLat',
            '2_stopLng','2_line','3_stopName','3_stopLat','3_stopLng','3_line'
            ]
polygonHeaderRow=header_row+['polypointlat','polypointlng','polyorder','polyid','exclude']



def calc_ave_indices(objList):
    #this doesn't quite work yet...need to experiment more with it.
    aveIndices = dict()
    i = 0
    for query in objList:
        mode = query.mode
        origin = query.originID
        time = query.timeOfDay
        ID=mode+"_"+str(origin)+query.railStation
        try:
            aveIndices[ID]['driveFactors'].append(query.driveFactor)
            aveIndices[ID]['totTime'].append(query.totTime)
            aveIndices[ID]['walkDistance'].append(query.walkDist)
            aveIndices[ID]['walkTime'].append(query.walkTime)
            #aveIndices[ID]['stations'].append(query.railStation)
            aveIndices[ID]['transfers'].append(query.numLines)
            try:
                aveIndices[ID]['stops'].append([query.stops[0][1][0],query.stops[0][1][1]])
            except (TypeError, IndexError):
                aveIndices[ID]['stops'].append([None,None])

        except:
            aveIndices[ID]={'driveFactors':[],'totTime':[],'walkDistance':[],'walkTime':[],'stations':[],
                            'transfers':[],'stops':[]}
            aveIndices[ID]['driveFactors'].append(query.driveFactor)
            aveIndices[ID]['totTime'].append(query.totTime)
            aveIndices[ID]['walkDistance'].append(query.walkDist)
            aveIndices[ID]['walkTime'].append(query.walkTime)
            #aveIndices[ID]['stations'].append(query.railStation)
            aveIndices[ID]['transfers'].append(query.numLines)
            try:
                aveIndices[ID]['stops'].append([query.stops[0][1][0],query.stops[0][1][1]])
            except (TypeError, IndexError):
                aveIndices[ID]['stops'].append([None,None])
    for ID in aveIndices:
        for item in aveIndices[ID].values():
            try:
                item=np.mean(item)
            except:
                print(item)
                try:
                    if len(set(item))>1:
                        if item[0]==item[1] or item[0]==item[2]:
                            item=item[0]
                        elif item[1]==item[2]:
                            item=item[1]
                        else:
                            item=item[1]
                except:
                    pass
                print(item,2)
    return aveIndices

def calc_min_indices(objList):
    minIndices = dict()
    i = 0
    for query in objList:
        mode = query.mode
        origin = query.originID
        time=query.timeOfDay
        UID=mode+"_"+str(origin)+"_"+str(time)
        try:
            if query.totTime<minIndices[UID][1]:
                minIndices[UID]=[i,query.totTime]
            else:
                pass
        except KeyError:
            minIndices[UID]=[i,query.totTime]
        i+=1
    return


def read_picklefiles(filename):
    with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\'+filename+'.p','rb') as picklefile:
        objectList=pickle.load(picklefile)
        picklefile.close()
    return objectList

def write_raw_datafiles(objectList,which='all'):
    if which=='all' or which == 'minave':
        try:
            minIndices=calc_min_indices(objectList)
            aveIndices=calc_ave_indices(objectList)
            #print(aveIndices)
        except NameError:
            print("error!")  #placeholder function...this block is really here to catch exceptions and direct to a previous
            minIndices={}
            # query stored in a pickle file.
            # read_picklefiles('201657_204')  #read in a previous pickle file

        with open(query_name+'_clean_min.csv','w') as outfile:
            writer = csv.writer(outfile, lineterminator='\n')
            writer.writerow(header_row)
            for row in minIndices.values():
                try:
                    writer.writerow(objectList[row[0]].line_to_write())
                except:
                    continue
            outfile.close()
        print(str(len(minIndices)),'cleaned queries successfully written out')

    if which == 'all' or which=="raw":
        #now write out the raw routes to a csv file...
        with open(query_name+'.csv','w') as outfile:
            writer=csv.writer(outfile, lineterminator='\n')
            writer.writerow(header_row)
            for row in objectList:
                try:
                    writer.writerow(row.line_to_write())
                except:
                    pass
        print(str(len(objectList))+' raw queries written')
    if which == 'all' or which =='pickle':
        # and finally, write out to a pickle file.  This might not work...
        with open(query_name+'.p','wb') as picklefile:
            pickle.dump(objectList,picklefile)
        print(str(len(objectList))+' queries written to pickle file')


