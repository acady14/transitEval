__author__ = 'acady'

import math
import googlemaps
from RouteClass import route
import datetime as dt
import random


def execute_query(origin,destination,travelMode,time,gmaps):
    directions_result = gmaps.directions(origin,
                                     destination,
                                     mode=travelMode,
                                     departure_time=time)
    return directions_result


def find_stations(origin, stationLocsll):
    first = [None,float(999999999)]
    second = [None,float(9999999999)]
    third = [None,float(99999999999)]
    for station in stationLocsll:
        # print(stationLocs[station][0])
        # print(origin[0])
        # print(abs(stationLocs[station][1])-abs(origin[1]))
        dist = math.sqrt((stationLocsll[station][0]-origin[0])**2+(abs(stationLocsll[station][1])-abs(origin[1]))**2)
        if station == "Downtown Santa Monica":  # we want to prefer going to downtown santa monica to break ties
            dist*=.75
        if dist<first[1]:
            third=second
            second=first
            first=[station,dist]
        elif dist<second[1]:
            third=second
            second=[station,dist]
        elif dist<third[1]:
            third=[station,dist]
    return([first[0],second[0],third[0]])



def data_pull(directionList,coordList, timesList,modeList,stationLocsll, stationLocsadd,limit,apikey):
    gmaps = googlemaps.Client(key=apikey)
    queryNum = 0
    rawList = list()
    objectList = list()
    originID = 0
    routeID = 0
    drive_time=float()

    print("starting connection with Google Maps")
    try:
        for direction in directionList:
            for origin in coordList[:]:
                if queryNum>limit:
                    break
                originID+=1
                destinations=find_stations(origin,stationLocsll)
                if type(origin)==type(tuple()):
                    origin=str(origin[0])+','+str(origin[1])
                try:
                    for destination in destinations:
                        if queryNum>limit:
                            break
                        #drive_time=dict()
                        routeID+=1
                        dest=stationLocsadd[destination]
                        for time in timesList:
                            qtime=dict()
                            for samp in range(0,3):
                                qtime[samp]=time+dt.timedelta(minutes=random.randint(samp*20,(samp+1)*20)) #randomize in 20 minute blocks
                            if queryNum>limit:
                                break
                            travelMode = "driving"
                            if direction == 'to_station':
                                rawToAppend = execute_query(origin,dest,travelMode,qtime[1],gmaps)
                            elif direction == 'from_station':
                                rawToAppend = execute_query(dest,origin,travelMode,qtime[1],gmaps)
                            rawList.append(rawToAppend)
                            Object = route(rawToAppend,travelMode.upper())
                            Object.railStation = destination
                            Object.exactTime = qtime[1].minute
                            Object.driveFactor = 1
                            Object.originID = originID
                            Object.routeID = routeID
                            Object.timeOfDay = time.hour
                            objectList.append(Object)
                            Object.direction = direction
                            drive_time = Object.totTime
                            if queryNum == 0:
                                print("connection established")
                            queryNum += 1
                            if queryNum % 500 == 0:
                                print(str(queryNum),' queries executed')
                        for travelMode in modeList:
                            routeID += 1
                            for time in timesList:
                                for samp in range(0,3):
                                    if direction == 'to_station':
                                        rawToAppend = execute_query(origin, dest, travelMode, qtime[samp], gmaps)
                                    elif direction == 'from_station':
                                        rawToAppend = execute_query(dest, origin, travelMode, qtime[samp], gmaps)
                                    rawList.append(rawToAppend)
                                    Object = route(rawToAppend,travelMode.upper())
                                    Object.railStation = destination
                                    Object.exactTime = qtime[samp].minute
                                    Object.driveFactor = float(Object.totTime)/drive_time  #note that the drive time is computed with samp==1
                                    Object.originID = originID
                                    Object.routeID = routeID
                                    Object.timeOfDay = time.hour
                                    Object.direction = direction
                                    objectList.append(Object)
                                    queryNum += 1
                                    if queryNum % 500 == 0:
                                        print(str(queryNum),' queries executed')
                except:
                    continue
    except:
        print("ERROR!")
        print("query number"+str(queryNum))
        print(destination,origin,time,direction)
        raise

    print(str(queryNum)+' queries complete')