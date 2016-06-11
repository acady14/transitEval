__author__ = 'acady'
'''
this file contains all functions relating to polygons, testing interior points, or other geometrical operations
'''
import csv
import numpy as np


def init_vectorList(polygon):
    # creates a list of vectors for the polygon of interest.  Each vector is from one vertex to
    # its counter-clockwise neighbor
    vectorList = []
    i = 0
    for point in polygon:
        try:
            vectorList.append((polygon[i+1][0]-point[0],polygon[i+1][1]-point[1]))
        except IndexError:
            vectorList.append((polygon[0][0]-point[0],polygon[0][1]-point[1]))
        i += 1
    return vectorList


def test_loc(testLoc,polygon,vectorList):
    # function prints 1 if the point is inside the polygon, 0 if outside
    for vector,point in zip(vectorList,polygon):
        pointvec = (testLoc[0]-point[0], testLoc[1]-point[1])
        cp = pointvec[0]*vector[1]-pointvec[1]*vector[0]
        if cp > 0:
            return False
    return True


def build_coord_list(polygon):
    #let's first define the outside edges of our box--no point will ever be outside of these
    box_NE = (max(polygon, key=lambda x: x[0])[0], max(polygon, key=lambda x: x[1])[1])
    box_NW = (max(polygon, key=lambda x: x[0])[0], min(polygon, key=lambda x: x[1])[1])
    box_SE = (min(polygon, key=lambda x: x[0])[0], max(polygon, key=lambda x: x[1])[1])
    box_SW = (min(polygon, key=lambda x: x[0])[0], min(polygon, key=lambda x: x[1])[1])

    vectorList = init_vectorList(polygon)
    coordList = []

    latList=np.arange(box_SW[0],box_NW[0],0.0018)  # in Los Angeles, this is about 200m
    longList=np.arange(box_NW[1],box_NE[1],0.0022)  # in Los Angeles, this is about 200m

    for lat in latList:
        for long in longList:
            if test_loc((lat,long),polygon,vectorList):
                coordList.append((lat,long))
    return coordList


def write_out_coordList(coordList):
    # optional function that writes out the coordinates list for inspection in Tableau
    with open('coordList.csv', 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        writer.writerow(["lat", "long"])
        for row in coordList:
            writer.writerow(row)
    print(str(len(coordList))+' coordinates to test and written out to file')


def calc_polygons_for_tableau(coordList):
    # this function takes the coordinates (a grid defined by the grain size) and makes a box around each so that they may
    # be represented by a GIS polygon layer in tableau.
    coordDict = {}
    for coord in coordList:
        boxcoords = list((coord[0]+0.0009,coord[1]-0.0011))
        boxcoords.append((coord[0]+0.0009, coord[1]+0.0011))
        boxcoords.append((coord[0]-0.0009, coord[1]+0.0011))
        boxcoords.append((coord[0]-0.0009, coord[1]-0.0011))
        coordDict[coord] = boxcoords
    return coordDict


def write_out_polygon_coords(coordDict):
    # optional function that writes out the coordinates list for the tableau-input polygons
    i = 1
    with open('coordList2.csv', 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        writer.writerow(["id", "lat", "long", "ptlat", "ptlong", "ptorder"])
        for key, val in coordDict.items():
            j = 1
            for item in val:
                row = list(i)
                row.append(key[0])
                row.append(key[1])
                row.append(item[0])
                row.append(item[1])
                row.append(j)
                writer.writerow(row)
                j += 1
            i += 1

    print('finished')


with open('C:\\Users\\acady\\Documents\\courses\\y2Q3\\ClientPA\\out.csv','r') as infile:
    reader = csv.reader(infile,  lineterminator='\n')
    header = next(reader)
    i = 0
    headerDict = dict()
    for item in header:
        headerDict[i] = item
        i += 1
    objList = list()
    for row in reader:
        tmpDict = dict()
        j = 0
        for item in row:
            tmpDict[headerDict[j]] = row[j]
            j += 1
        objList.append(tmpDict)

def insert_polygons(coordDict, objList):
    coordDictbu1 = dict(coordDict)
    outList = list()
    x = 0
    fileLength = float(len(objList))
    for obj in objList:
        x += 1
        if x % 500 == 0:
            print(str(round(float(x)/fileLength, 2)), "% complete")
        i = -1
        for loc,polygon in coordDict.items():
            i += 1
            point=(float(obj['originloclat']), float(obj['originloclng']))
            if abs(point[0]-loc[0]) > 0.003:
                continue
            if abs(point[1]-loc[1]) > 0.003:
                continue
            vectorList = init_vectorList(polygon)
            if test_loc(point,polygon, vectorList):
                j = 1
                for vertex in polygon:
                    obj['polypointlat'] = vertex[0]
                    obj['polypointlng'] = vertex[1]
                    obj['polyorder'] = j
                    obj['polyid'] = i
                    j += 1
                    outList.append(dict(obj))
                break

    print('finished')


    outList2 = list()
    for direction in ['from_station', 'to_station']:
        loctestDict = dict()
        i = -1
        for obj in outList:
            i += 1
            if obj['direction'] not in direction:
                continue
            try:
                if len(loctestDict[obj['polyid']]) < 4:
                    loctestDict[obj['polyid']].append(obj)
                    outList2.append(obj)
                    obj['exclude']=0
                else:
                    obj['exclude']=1  #this is a flag for display purposes--a few times we only want to display
                                      # one polygon.  this gives a flag to easily exclude if multiple polygons overlap
            except KeyError:
                loctestDict[obj['polyid']] = [obj]
                outList2.append(obj)
                obj['exclude'] = 0

