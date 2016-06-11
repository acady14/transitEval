__author__ = 'acady'


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
