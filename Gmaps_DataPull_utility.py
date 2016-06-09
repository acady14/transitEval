
# coding: utf-8

# In[1]:

import googlemaps
import json
import time
import csv
import math
import numpy as np
import datetime as dt
import pickle
import random

query_name=str(dt.datetime.now().year)
query_name+=str(dt.datetime.now().month)
query_name+=str(dt.datetime.now().day)
query_name+=("_")
query_name+=(str(dt.datetime.now().hour))
query_name+=(str(dt.datetime.now().minute))
print(query_name)

# this first block initializes some information
gmaps = googlemaps.Client(key='AIzaSyD_-Xexo79jeQhPrvwrrltW4lbdlcFQs8Y')
modeList=['transit']#,'bicycling']
#largest times list
# timesList=(dt.datetime(2016,4,16,5),dt.datetime(2016,4,16,8),
#            dt.datetime(2016,4,16,10),dt.datetime(2016,4,16,12),
#            dt.datetime(2016,4,16,16),dt.datetime(2016,4,16,18),
#            dt.datetime(2016,4,16,20))

#smaller times list used for demonstration
# timesList=(dt.datetime(2016,5,16,5),dt.datetime(2016,5,16,8),
#            dt.datetime(2016,5,16,12),
#            dt.datetime(2016,5,16,16),
#            dt.datetime(2016,5,16,20))

#Time to use for current pull...COMPLETED TIMES:
timesList=(dt.datetime(2016,6,16,7),)

#Polygon #1: Jakub's initial polygon based on estimates of BBB primary catchment area
# oldPolygon=[(34.035502,-118.535724),
#          (34.078244,-118.439367),
#          (34.027825,-118.388888),
#          (33.945030,-118.369774),
#          (33.950658,-118.447867)]

#Polygon #2:  this polygon encompasses 3 miles north of Expo line stations and 4 miles south
polygon=[(34.036763,-118.534884),
             (34.057280,-118.500412),
             (34.079303,-118.440661),
             (34.067740,-118.403639),
             (34.029623,-118.388831),
             (33.967029,-118.394050),
             (33.965821,-118.456077)
           ]  
# Pacific Pallisades polygon:  used to add data on 18 may.  
#polygon=[(34.039321,-118.558733),(34.053758,-118.529421),(34.048140,-118.517105),(34.036050,-118.536159)]


#Polygon #3: used for testing a small area around the SM Airport
# polygon=[(34.017154,-118.481657),(34.026829, -118.452217),
#          (34.019893,-118.428656),(34.002568,-118.448183),(34.004018,-118.476110)]

global stationLocs

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

#direction='to_station'
#direction='from_station'
directionList=['to_station','from_station']


# In[2]:


class route:
    def __init__(self,result,inputMode=None):
        if inputMode is None:
            if result[0]['legs'][0]['steps'][0]['travel_mode']=="DRIVING":
                self.mode="DRIVING"
            elif result[0]['legs'][0]['steps'][0]['travel_mode']=="WALKING":
                self.mode="TRANSIT"  
            elif result[0]['legs'][0]['steps'][0]['travel_mode']=="BICYCLING":
                self.mode="BICYCLING"
        else:
            self.mode=inputMode
        try:
            try:
                self.originAddress=result[0]['legs'][0]['start_address']
            except IndexError:
                self.originAddress=None
        except KeyError:
            self.originAddress=None
        self.direction=str()
        self.originLoc=(result[0]['legs'][0]['start_location']['lat'],result[0]['legs'][0]['start_location']['lng'])
        try:
            self.endAddress=result[0]['legs'][0]['end_address']
        except KeyError:
            self.endAddress=None
        self.endLoc=(result[0]['legs'][0]['end_location']['lat'],result[0]['legs'][0]['end_location']['lng'])
        self.totDist=result[0]['legs'][0]['distance']['value']
        self.totTime=result[0]['legs'][0]['duration']['value']
        self.closestStation=str()
        self.driveFactor=0
        self.originID=int()
        self.routeID=int()
        self.timeOfDay=int()
        self.exactTime=int()
        if self.mode=="DRIVING":
            uberFare=max(1.65+(self.totDist/1609.3)*0.9+(self.totTime/60)*0.15,4.65)
            self.totTime=result[0]['legs'][0]['duration_in_traffic']['value']
        else:
            uberFare=None
        if self.mode=="TRANSIT":
            self.numLines=0
            self.walkTime=0
            self.walkDist=0
            self.busTime=0
            self.busDist=0
            self.stops=list()
            self.lines=list()
            self.agencies=set()
            try:
                self.fare=result[0]['fare']['value']
            except KeyError:
                self.fare=None
            tmpFare=0.00
            totalDuration=0
            for step in result[0]['legs'][0]['steps']:
                totalDuration+=step['duration']['value']
                tmpmode=step["travel_mode"]
                if tmpmode=="WALKING":
                    self.walkTime+=step['duration']['value']
                    self.walkDist+=step['distance']['value']
                    #print(tmpmode,stepDuration,stepDistance)
                elif tmpmode=="TRANSIT":
                    stopName=step['transit_details']['departure_stop']['name']
                    stopLoc=(step['transit_details']['departure_stop']['location']['lat'],step['transit_details']['departure_stop']['location']['lng'])
                    #print('stop details: ',stopName,stopLoc[0],stopLoc[1])
                    self.stops.append([stopName,stopLoc])
                    agencyName=step['transit_details']['line']['agencies'][0]['name']
                    if agencyName=="Culver CityBus":
                        tmpFare+=1.00
                    elif agencyName=="Metro - Los Angeles":
                        tmpFare+=1.75
                    elif agencyName=="Big Blue Bus":
                        tmpFare+=1.25
                    elif agencyName=="LADOT":
                        tmpFare+=0.50
                    try:
                        lineName=step['transit_details']['line']['short_name']
                        if lineName=="R10":
                            tmpFare+=1.25
                    except KeyError:
                        try:
                            lineName=step['transit_details']['line']['name']
                        except KeyError:
                            lineName=''
                    self.lines.append(agencyName+' '+lineName)
                    self.agencies.update([agencyName])
                    self.busTime+=step['duration']['value']
                    self.busDist+=step['distance']['value']
                    self.numLines+=1
            if self.fare==None:
                self.fare=tmpFare
                    #print('fare',self.fare)
            self.numLines=len(self.lines)
            if self.numLines==0:
                self.agencies=set("walk")
                self.lines=["walk to station"]
            self.waitTime=result[0]['legs'][0]['duration']['value']-totalDuration 
            if self.waitTime<=0:
                self.waitTime==0  #this is likely due to an error in google's DB.  
        else:
            self.numLines=None
            self.walkTime=None
            self.walkDist=None
            self.busTime=None
            self.busDist=None
            self.stops=None
            self.lines=None
            self.agencies=None
            self.fare=uberFare
            self.waitTime=None

    def line_to_write(self):
        ltw=list()
        ltw.append(self.driveFactor)
        ltw.append(self.originID)
        ltw.append(self.routeID)
        ltw.append(self.originAddress)
        ltw.append(self.direction)
        ltw.append(self.originLoc[0])
        ltw.append(self.originLoc[1])
        ltw.append(self.endAddress)
        ltw.append(self.endLoc[0])
        ltw.append(self.endLoc[1])        
        ltw.append(self.totDist)
        ltw.append(self.totTime)
        ltw.append(self.railStation)
        ltw.append(self.mode)
        ltw.append(self.timeOfDay)
        ltw.append(self.exactTime)
        ltw.append(self.numLines)
        ltw.append(self.walkTime)
        ltw.append(self.walkDist)
        ltw.append(self.busTime)
        ltw.append(self.busDist)
        ltw.append(self.agencies)
        ltw.append(self.fare)
        ltw.append(self.waitTime)
        for stop in [0,1,2]:
            try:
                ltw.append(self.stops[stop][0])
                ltw.append(self.stops[stop][1][0])
                ltw.append(self.stops[stop][1][1])
                ltw.append(self.lines[stop])
            except:
                ltw.append(None)
                ltw.append(None)
                ltw.append(None)
                ltw.append(None)
        return ltw



# In[3]:

#this cell generates a list of coordinates (in a grid patttern) inside of the polygon that you specify 
#in the first cell.  grid is at at 200m increments.

def init_vectorList(polygon):
    vectorList=[]
    i=0
    for point in polygon:
        try:
            vectorList.append((polygon[i+1][0]-point[0],polygon[i+1][1]-point[1]))
        except IndexError:
            vectorList.append((polygon[0][0]-point[0],polygon[0][1]-point[1]))
        i+=1   
    return vectorList
    


def test_loc(testLoc,polygon,vectorList):
    #function prints 1 if the point is inside the polygon, 0 if outside
    for vector,point in zip(vectorList,polygon):
        pointvec=(testLoc[0]-point[0],testLoc[1]-point[1])
        #cp=calc_cross_product(pointvec,vector)
        cp=pointvec[0]*vector[1]-pointvec[1]*vector[0]
        if cp>0:
            return False
    return True



#let's first define the outside edges of our box--no point will ever be outside of these
box_NE=(max(polygon,key=lambda x: x[0])[0],max(polygon,key=lambda x: x[1])[1])
box_NW=(max(polygon,key=lambda x: x[0])[0],min(polygon,key=lambda x: x[1])[1])
box_SE=(min(polygon,key=lambda x: x[0])[0],max(polygon,key=lambda x: x[1])[1])
box_SW=(min(polygon,key=lambda x: x[0])[0],min(polygon,key=lambda x: x[1])[1])

vectorList=init_vectorList(polygon)
coordList=[]

latList=np.arange(box_SW[0],box_NW[0],0.0018)
longList=np.arange(box_NW[1],box_NE[1],0.0022)
# latList=np.arange(box_SW[0],box_NW[0],0.0085)
# longList=np.arange(box_NW[1],box_NE[1],0.01)

for lat in latList:
    for long in longList:
        if test_loc((lat,long),polygon,vectorList):
            coordList.append((lat,long))

#optinal function that writes out the coordinates list for inspection in Tableau
with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\coordList.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    writer.writerow(["lat","long"])
    for row in coordList:
        writer.writerow(row)
        
print(str(len(coordList))+' coordinates to test')




# In[4]:

def execute_query(origin,destination,travelMode,time):
    directions_result = gmaps.directions(origin,
                                     destination,
                                     mode=travelMode,
                                     departure_time=time)
    return directions_result


def find_stations(origin,stationLocsll):
    first=[None,float(999999999)]
    second=[None,float(9999999999)]
    third=[None,float(99999999999)]
    for station in stationLocsll:
        #print(stationLocs[station][0])
        #print(origin[0])
        #print(abs(stationLocs[station][1])-abs(origin[1]))
        dist=math.sqrt((stationLocsll[station][0]-origin[0])**2+(abs(stationLocsll[station][1])-abs(origin[1]))**2)
        if station=="Downtown Santa Monica":  #we want to prefer going to downtown santa monica to break ties
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


queryNum=0
rawList=list()
objectList=list()
originID=0
routeID=0
limit=120000
# if direction=='from_station':
#     tmpCoordList=coordList.copy()
#     tmpDestinations=destinations.copy()
#     coordList=tmpDestinations
#     destinations=tmpCoordList
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
                        travelMode="driving"
                        if direction=='to_station':
                            rawToAppend=execute_query(origin,dest,travelMode,qtime[1])
                        elif direction=='from_station':
                            rawToAppend=execute_query(dest,origin,travelMode,qtime[1])
                        rawList.append(rawToAppend)
                        Object=route(rawToAppend,travelMode.upper())
                        Object.railStation=destination
                        Object.exactTime=qtime[samp].minute
                        Object.driveFactor=1
                        Object.originID=originID
                        Object.routeID=routeID
                        Object.timeOfDay=time.hour
                        #drive_time[time.hour]=float(Object.totTime)
                        drive_time=Object.totTime
                        objectList.append(Object)
                        Object.direction=direction
                        if queryNum==0:
                            print("connection established")
                        queryNum+=1
                        if queryNum%100==0:
                            print(str(queryNum),' queries executed')       
                    for travelMode in modeList:
                        routeID+=1
                        for time in timesList:
                            for samp in range(0,3):
                                if direction=='to_station':
                                    rawToAppend=execute_query(origin,dest,travelMode,qtime[samp])
                                elif direction=='from_station':
                                    rawToAppend=execute_query(dest,origin,travelMode,qtime[samp])
                                rawList.append(rawToAppend)
                                Object=route(rawToAppend,travelMode.upper())
                                Object.railStation=destination
                                Object.exactTime=qtime[samp].minute
                                #Object.driveFactor=float(Object.totTime)/drive_time[time.hour]
                                Object.driveFactor=float(Object.totTime)/drive_time  #note that the drive time is computed with samp==1
                                Object.originID=originID
                                Object.routeID=routeID
                                Object.timeOfDay=time.hour
                                Object.direction=direction
                                objectList.append(Object)
                                queryNum+=1
                                if queryNum%100==0:
                                    print(str(queryNum),' queries executed')
            except:
                continue
except:
    print("ERROR!")
    print("query number"+str(queryNum))
    print(destination,origin,time,direction)
    raise

print(str(queryNum)+' queries complete')


# In[5]:

#this cell manages the writing out of the formatted results



header_row=[ 'driveFactor','origin id','route id','originAddress','direction','originLoc lat','originLoc lng','endAddress',
            'end lat','end lng','totDist', 'totTime', 'railStation', 'mode','time of day','exact time','numLines',
             'walkTime', 'walkDist','busTime','busDist','agencies',
            'fare','waitTime','1_stopName','1_stopLat','1_stopLng','1_line','2_stopName','2_stopLat',
            '2_stopLng','2_line','3_stopName','3_stopLat','3_stopLng','3_line'
            ]


def calc_min_indices(objList):
    minIndices=dict()
    i=0
    for query in objList:
        mode=query.mode
        origin=query.originID
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
    return minIndices
def read_picklefiles(filename):
    with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\'+filename+'.p','rb') as picklefile:
        objectList=pickle.load(picklefile)
        picklefile.close()
    return objectList

def calc_ave_indices(objList):
    aveIndices=dict()
    i=0
    for query in objList:
        mode=query.mode
        origin=query.originID
        time=query.timeOfDay
        ID=mode+"_"+str(origin)+_query.railStation
        try:
            aveIndices[ID]['driveFactors'].append(query.driveFactor)
            aveIndices[ID]['totTime'].append(query.totTime)
            aveIndices[ID]['walkDistance'].append(query.walkDist)
            aveIndices[ID]['walkTime'].append(query.walkTime)
            #aveIndices[ID]['stations'].append(query.railStation)
            aveIndices[ID]['transfers'].append(query.numLines)
            try:
                aveIndices[ID]['stops'].append([query.stops[0][1][0],query.stops[0][1][1]])
            except (TypeError, indexError):
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

            


try:
    minIndices=calc_min_indices(objectList)
    aveIndices=calc_ave_indices(objectList)
    #print(aveIndices)
except NameError:
    read_picklefiles('201657_204')

with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\'+query_name+'_clean_min1.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    writer.writerow(header_row)
    for row in minIndices.values():
        try:
            writer.writerow(objectList[row[0]].line_to_write())   
        except:
            continue
    outfile.close()
print(str(len(minIndices)),'cleaned routes successfully written out')

# with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\'+query_name+'_clean_ave.csv','w') as outfile:
#     writer=csv.writer(outfile, lineterminator='\n')
#     writer.writerow(header_row)
#     for row in aveIndices.values():
#         try:
#             writer.writerow(objectList[row[0]].line_to_write())   
#         except:
#             continue
#     outfile.close()
# print(str(len(aveIndices)),'cleaned routes successfully written out')

with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\'+query_name+'1.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    writer.writerow(header_row)
    for row in objectList:
        try:
            writer.writerow(row.line_to_write())
        except:
            pass
with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\'+query_name+'.p','wb') as picklefile:
    pickle.dump(objectList,picklefile)
    picklefile.close()
print(str(len(objectList))+' queries written')


# In[6]:

# unused code
'''
numList=range(700,800,50)
streetList=list(range(2,4))
for i in range(len(streetList)):
    if i==0:
        streetList[i]=str(i+2)+'nd st'
    elif i==1:
        streetList[i]=str(i+2)+'rd st'
    elif i==6:
        streetList[i]='Lincoln Blvd'
    elif i==11:
        streetList[i]='Euclid St'
    else:
        try:
            streetList[i]=str(i+2)+'th st'
        except TypeError:
            continue
            
addressList=list()

for street in streetList:
    for num in numList:
        addressList.append(str(num)+' '+street+' '+'Santa Monica, CA')
   
   
   
   
   # directions_result = gmaps.directions('850 3rd st Santa Monica',
#                                  '2525 Michigan Ave, Santa Monica, CA 90404',
#                                  mode='transit',
#                                  departure_time=dt.now())
   
   # def calc_cross_product(vec1,vec2):
#     cr_prod=vec1[0]*vec2[1]-vec1[1]*vec2[0]
#     return cr_prod

#     print(mode, time)
#     stps=directions_result[0]['legs'][0]['steps']
#     i=0
#     for step in stps:
#         i+=1
#         print(' ')
#         print('step number '+str(i))
#         #print(step)
#         print(step['travel_mode'])
#         print(step['distance']['text'])
#         print(step['duration']['text'])
#         if step['travel_mode']=='TRANSIT':
#             print(step['transit_details']['line']['name']+' '+step['transit_details']['line']['short_name'])
#             print('starts at: '+step['transit_details']['departure_stop']['name'])
#             print('arrives at: '+step['transit_details']['arrival_stop']['name'])
            

            
            
#         print('distance: '+str(directions_result[0]['legs'][0]['distance']['value'])+" meters")
#         print('duration: '+str(directions_result[0]['legs'][0]['duration']['text']))

#         try:
#             traffic_time=directions_result[0]['legs'][0]['duration_in_traffic']['value']-directions_result[0]['legs'][0]['duration']['value']
#             print('traffic delay: '+str(traffic_time)+" seconds")
#         except KeyError:
#             pass
#         print('')

# for item in directions_result[0]:
#     print(item) 
#     #for thing in directions_result[0][item]:
#     #    print(thing)
#     print('')
#     if result[0]['legs'][0]['steps'][1]['travel_mode']=="TRANSIT":
#         print('transit mode...engage!')
# #     else:
#         print(' ')
#         continue
#     stepNum=0
#     totalDuration=0
#     print(result[0]['legs'][0]['start_address'])
#     for step in result[0]['legs'][0]['steps']:
#         totalDuration+=step['duration']['value']
#         mode=step["travel_mode"]
#         if mode=="WALKING":
#             stepDuration=step['duration']['value']
#             stepDistance=step['distance']['value']
#             #print(mode,stepDuration,stepDistance)
#         elif mode=="TRANSIT":
#             stopName=step['transit_details']['departure_stop']['name']
#             stopLoc=(step['transit_details']['departure_stop']['location']['lat'],step['transit_details']['departure_stop']['location']['lng'])
#             print('stop details: ',stopName,stopLoc[0],stopLoc[1])
#             agencyName=step['transit_details']['line']['agencies'][0]['name']
#             lineName=step['transit_details']['line']['short_name']
#             print('line details: ',agencyName,lineName)
#             stepDuration=step['duration']['value']
#             stepDistance=step['distance']['value']
#             print(mode,stepDuration,stepDistance)
#             print('fare',result[0]['fare']['value'])
#     waitTime=result[0]['legs'][0]['duration']['value']-totalDuration
#     print(str(waitTime),' seconds waiting, ',str(round(float(waitTime)/float(totalDuration),3)*100),' percent of time waiting')
    oldheader_row=['origin',
            'destination',
            'conveyance',
            'distance',
            'duration',
            'time of day',
            'driving factor'
           ]        
    if type(origin)==type(tuple()):
        origin=str(origin[0])+','+str(origin[1])
    for destination in destinations:
        dest=stationLocs[destination]
        if i>14:
            break
        row_to_write, rawToAppend=execute_query(origin,destination,'driving',dt.datetime.now())
        row_to_write.append(1)
        rawList.append(rawToAppend)
        drive_time=float(row_to_write[4])
        outList.append(row_to_write)
        i+=1
        for travelMode in modeList:
            row_to_write, rawToAppend=execute_query(origin,destination,travelMode,dt.datetime.now())
            row_to_write.append(float(row_to_write[4])/drive_time)
            outList.append(row_to_write)
            rawList.append(rawToAppend)
            i+=1   
def execute_query(origin,destination,travelMode,time):
    directions_result = gmaps.directions(origin,
                                     stationLocs[destination],
                                     mode=travelMode,
                                     departure_time=time)
    row_to_write=list()
    row_to_write.append(origin)
    row_to_write.append(destination)
    row_to_write.append(travelMode)
    row_to_write.append(directions_result[0]['legs'][0]['distance']['value'])
    row_to_write.append(directions_result[0]['legs'][0]['duration']['value'])
    row_to_write.append(time.hour)
    row_to_write
    return row_to_write, directions_result
    # i=0
# for result in rawList: 
#     print('')
#     i+=1
#     z=0
#     for step in result[0]['legs'][0]['steps']:
#         z+=1
#         print(str(i)+"     "+str(z)+"            "+str(step))
                #@print(len(subItem))
            #print(str(i)+' '+str(key)+' '+str(len(thing[key])))



# outList2=list()   
# for item in rawList:
#     row_to_write=list()  
#     print(obj.line_to_write())
# #     for a in dir(obj):
#         if not a.startswith('__') and not callable(getattr(obj,a)):
#             row_to_write.append(getattr(obj,a))
#     outList2.append(row_to_write)
            with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\2016424_2029.p','rb') as picklefile:
    objectList=pickle.load(picklefile)
    picklefile.close()
    
print(str(len(rawList))+' queries read')
minIndices=dict()
i=0
for query in objectList:
    mode=query.mode
    origin=query.originID
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

with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\queries\\2016424_2029_clean.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    writer.writerow(header_row)
    for row in minIndices.values():
        writer.writerow(objectList[row[0]].line_to_write())   
    outfile.close()
print(str(len(minIndices)),'files successfully written out')
   stationDict={"downtown Santa Monica":'1601 4th St, Santa Monica, CA',
             "17th St-SMC":'1601 17th St, Santa Monica, CA',
             "26th-Bergamont Station":'2525 Michigan Ave, Santa Monica, CA'} 
'''


# In[7]:

import googlemaps
import datetime as dt
gmaps = googlemaps.Client(key='AIzaSyD_-Xexo79jeQhPrvwrrltW4lbdlcFQs8Y')
    
directions_result = gmaps.directions('401 Santa Monica Pier, Santa Monica, CA 90401',
                                  (34.013666,-118.490970),
                                  mode='transit',
                                  departure_time=dt.datetime.now())
print(directions_result)


# In[4]:

import numpy as np
import csv

polygon=[(34.036763,-118.534884),
             (34.057280,-118.500412),
             (34.079303,-118.440661),
             (34.067740,-118.403639),
             (34.029623,-118.388831),
             (33.967029,-118.394050),
             (33.965821,-118.456077)
           ]  

def init_vectorList(polygon):
    vectorList=[]
    i=0
    for point in polygon:
        try:
            vectorList.append((polygon[i+1][0]-point[0],polygon[i+1][1]-point[1]))
        except IndexError:
            vectorList.append((polygon[0][0]-point[0],polygon[0][1]-point[1]))
        i+=1   
    return vectorList
    


def test_loc(testLoc,polygon,vectorList):
    #function prints 1 if the point is inside the polygon, 0 if outside
    for vector,point in zip(vectorList,polygon):
        pointvec=(testLoc[0]-point[0],testLoc[1]-point[1])
        #cp=calc_cross_product(pointvec,vector)
        cp=pointvec[0]*vector[1]-pointvec[1]*vector[0]
        if cp>0:
            return False
    return True



#let's first define the outside edges of our box--no point will ever be outside of these
box_NE=(max(polygon,key=lambda x: x[0])[0],max(polygon,key=lambda x: x[1])[1])
box_NW=(max(polygon,key=lambda x: x[0])[0],min(polygon,key=lambda x: x[1])[1])
box_SE=(min(polygon,key=lambda x: x[0])[0],max(polygon,key=lambda x: x[1])[1])
box_SW=(min(polygon,key=lambda x: x[0])[0],min(polygon,key=lambda x: x[1])[1])

vectorList=init_vectorList(polygon)
coordList=[]

latList=np.arange(box_SW[0],box_NW[0],0.0018)
longList=np.arange(box_NW[1],box_NE[1],0.0022)
# latList=np.arange(box_SW[0],box_NW[0],0.0085)
# longList=np.arange(box_NW[1],box_NE[1],0.01)

for lat in latList:
    for long in longList:
        if test_loc((lat,long),polygon,vectorList):
            coordList.append((lat,long))

#optinal function that writes out the coordinates list for inspection in Tableau
with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\coordList.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    writer.writerow(["lat","long"])
    for row in coordList:
        writer.writerow(row)
        
print(str(len(coordList))+' coordinates to test')


# In[86]:

coordDict={}
for coord in coordList:
    boxcoords=list()
    boxcoords=[(coord[0]+0.0009,coord[1]-0.0011)]
    boxcoords.append((coord[0]+0.0009,coord[1]+0.0011))
    boxcoords.append((coord[0]-0.0009,coord[1]+0.0011))
    boxcoords.append((coord[0]-0.0009,coord[1]-0.0011))
    coordDict[coord]=boxcoords
i=1
with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\coordList2.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    writer.writerow(["id","lat","long","ptlat","ptlong","ptorder"])
    for key,val in coordDict.items():
        j=1
        for item in val:
            row=[i]
            row.append(key[0])
            row.append(key[1])
            row.append(item[0])
            row.append(item[1])
            row.append(j)
            writer.writerow(row)
            j+=1
        i+=1


print('finished')


# In[108]:

with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\out.csv','r') as infile:
    reader=csv.reader(infile,  lineterminator='\n')
    header=next(reader)
    i=0
    headerDict=dict()
    for item in header:
        headerDict[i]=item
        i+=1
    objList=list()
    for row in reader:
        tmpDict=dict()
        j=0
        for item in row:
            tmpDict[headerDict[j]]=row[j]
            j+=1
        objList.append(tmpDict)
coordDictbu1=dict(coordDict)
coordDictbu2=dict(coordDict)
outList=list()
x=0
print(len(objList))
for obj in objList:
    x+=1
    if x%500==0:
        print(x)
    i=-1
    for loc,polygon in coordDict.items():
        i+=1
        point=(float(obj['originloclat']),float(obj['originloclng']))
        if abs(point[0]-loc[0])>0.003:
            continue
        if abs(point[1]-loc[1])>0.003:
            continue
        vectorList=init_vectorList(polygon)
        if test_loc(point,polygon,vectorList):
            j=1
            for vertex in polygon:
                obj['polypointlat']=vertex[0]
                obj['polypointlng']=vertex[1]
                obj['polyorder']=j
                obj['polyid']=i
                j+=1
                outList.append(dict(obj))
            break
        
#     try:
#         coordDict.pop(loc)
#     except KeyError:
#         if coordDictbu1 is not None:
#             coordDict=dict(coordDictbu1)
#             coordDictbu1=None
#         else:
#             print('mushkila')
                
print('finished')
            
    


# In[109]:

j=len(headerDict)
newHeaderDict=dict(headerDict)
newHeaderDict[j]='polypointlat'
newHeaderDict[j+1]='polypointlng'
newHeaderDict[j+2]='polyorder'
newHeaderDict[j+3]='polyid'
newHeaderDict[j+4]='exclude'

outList2=list()
for direction in ['from_station','to_station']:
    loctestDict=dict()
    i=-1
    for obj in outList:
        i+=1
        if obj['direction'] not in direction:
            continue
        try:
            if len(loctestDict[obj['polyid']])<4:
                loctestDict[obj['polyid']].append(obj)
                outList2.append(obj)
                obj['exclude']=0
            else:
                obj['exclude']=1
        except KeyError:
            loctestDict[obj['polyid']]=[obj]
            outList2.append(obj)
            obj['exclude']=0
    testout=0
    for item,val in loctestDict.items():
        if len(val)>4:
            testout+=1
    print(testout,direction)
    
        

i=0
with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\polygonoutputMay.csv','w') as outfile:
    writer=csv.writer(outfile, lineterminator='\n')
    r2w=list()
    for num in range(len(newHeaderDict)):
        r2w.append(newHeaderDict[num])
    writer.writerow(r2w)
    for row in outList:
        r2w=list()
        for num in range(len(newHeaderDict)):
            r2w.append(row[newHeaderDict[num]])
        i+=1
        writer.writerow(r2w)
print('finished',str(i))
            


# In[104]:



