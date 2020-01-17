'''
    Calculation of offsets between local minima and river
    axes. Results will be dumped in a csv table

    Coding for Python 2.7
    Version: Nov, 15
'''
# imports
import os
import math
import string
import arcpy
import csv

# shortcut
pi = math.pi

# functions to check if subdirectory exists
def createSubdir(workspace, subdirList):
    for subdir in subdirList:
        if not os.path.isdir(workspace + '/' + subdir):
            #s.mkdir(workspace + '/' + subdir)
            os.mkdir(os.path.join(workspace, subdir))

# enforces the use of the right extension of inName (cambia la extensión de un documento a una extensión deseada)
def controlExtension(inName, ext):
    if inName.rfind('.') > 0:
        return inName[:inName.find('.')] + ext
    else:
        return inName + ext

#join project directory, subdrs and file names into complete paths
def completePath(workspace,subdir,nameList):
    for ix in range(len(nameList)):
        nameList[ix] = workspace + '/' + subdir + '/' + nameList[ix]
    return nameList

#check whether a file exists under a given path
def checkExistence(pathList):
    check = True
    for data in pathList:
        if not arcpy.Exists(data):
            check = False
            print ('! dataset ' + data + 'is missing')
            break
    return check

#extracts the filed names from any ESRI data set (stand alone table,
#shapefile, ...)
def getFieldNames(table):
    fnames = []
    fields = arcpy.ListFields(table)
    if fields:
        for field in fields:
            fnames.append(field.name)
    return fnames

#remove some fields by specifying the names that want to be kept
def cleanUpFields(table, keepFields):
    delFields = list ( set(getFieldNames(table) [2:])-
                       set(keepFields))
    arcpy.DeleteField_management(table, delFields)
    print (delFields)
    
#find center of lines
def getCenter(inFC):
    centres = []
    fieldList = ['SHAPE@XY']
    with arcpy.da.SearchCursor(inFC, fieldList) as cur:
        for row in cur:
            centres.append(row[0])
    return centres

#break all features into elementary segments
def splitPolyLineIntoSegments(inFC, outFC):
    arcpy.SplitLine_management(inFC, outFC)

#extract rather start or end of our segments
def getEndPoints(inFC, flag):
    ends = []
    fieldList = ['SHAPE@']
    with arcpy.da.SearchCursor(inFC, fieldList) as cur:
        if flag == 'START':
            for row in cur:
                ends.append((row[0].firstPoint.X, row[0].firstPoint.Y))
        elif flag == 'END':
            for row in cur:
                ends.append((row[0].lastPoint.X, row[0].lastPoint.Y))
    return ends

#get the bearing from two points on the segments
def getOrient(cpoints, epoints):
    orient = []
    
    if len(cpoints) != len(epoints):
        print ('! list lengths not identical')
        return orient
    for ix in range(len(cpoints)):
        pnt0 = cpoints[ix]
        pnt1 = epoints[ix]
        orient.append(math.atan2(pnt1[1]-pnt0[1], pnt1[0]-pnt0[0]))
    return orient

#calculate profile points
#pntd = point distance
#npnts = number of points per profile
def calcprofPoints(cPnts, angles, npnts, pntd):
    prof = []
    ix0 = 0

    for cen in cPnts:
        for ix1 in range(npnts + 1):
            dx = pntd * ix1 * math.cos(angles[ix0] + pi/2.)
            dy = pntd * ix1 * math.sin(angles[ix0] + pi/2.)
            xn = cen[0] + dx
            yn = cen[1] + dy
            prof.append( (xn, yn) )

            if ix1 > 0:
                xn = cen[0] - dx
                yn = cen[1] - dy
                prof.append( (xn, yn) )
                 
        ix0 += 1

    return prof
        
#convert calculated profile points into shapefile
def createEmptyShapefile(folder, name, spatReference):
    arcpy.CreateFeatureclass_management(folder, name, 'POINT', '', 
                                        'DISABLED', 'DISABLED', 
                                        spatReference)
     
#
def populatePointShape(pnts, npnts, FieldName, outFC):
    fieldList = ["SHAPE@XY", FieldName]

    with arcpy.da.InsertCursor(outFC, fieldList) as cur:
        ix0 = 0
        pperprof = npnts * 2 + 1
        for pnt in pnts:
            cur.insertRow( [pnt, ix0//pperprof] )
            ix0 += 1
    
#give a path to the file until extention
def recycleName(inPath): 
    return inPath[:inPath.find(".")] + 't' + inPath[inPath.find("."):]

#create 3D features by interpolating z-values from a surface (puts floating somethere above points/lines on a surface )
def convert3D(inFC, inGrid):
    outFC = recycleName(inFC)
    arcpy.InterpolateShape_3d(inGrid, inFC, outFC)
    arcpy.Delete_management(inFC)
    arcpy.Rename_management(outFC, inFC)
    
#calculate shift triples (3D tuple)
def calcShiftTriples (inFC, FieldName, zdif):
    shifts = []
    fieldList = ["SHAPE@", FieldName]
    
    with arcpy.da.SearchCursor(inFC, fieldList) as cur:
        ip = -1 #profile point number?
        for row in cur:
            x = row[0].firstPoint.X
            y = row[0].firstPoint.Y
            z = row[0].firstPoint.Z
            i = row[1]
            
            if i != ip:
                if ip != -1:
                    if c[2]-m[2] > zdif: shifts.append(c + m)
                c = (x, y, z)
                m = c
                ip = i
            elif i == ip and z < m[2]:
                m = (x, y, z)
        
    shifts.append(c + m)
    return shifts

#create a csv as output
def tabularOutput(fileName, stuples):
    with open(fileName, 'wb') as csvfile:
        tabwriter = csv.writer(csvfile, delimiter = ' ',
                               quoting=csv.QUOTE_MINIMAL)
        ix = 0
        for t in stuples:
            tabwriter.writerow( (ix, t[0], t[1], t[3], t[4]) )
            ix += 1
        
#####################################
    
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("3D")

workspace = 'C:/Users/User/YandexDisk/Studying/TUD/GIS-Applications-Python/Task1'
subdirList = ['Temp','Shape', 'Grid', 'Output']
inFCName = 'r.shp'
inGridName = 'DGM2s.tif'
segFCName = 'seg.shp'
profFCName = 'prof.shp'
nPoints = 4
pDist = 1.5
outTabName = 'offset.csv'
zdif = 0.05

createSubdir(workspace,subdirList)
inFCName = controlExtension (inFCName, '.shp')
inFC = completePath(workspace,'Shape',[inFCName])[0]
inGrid = completePath(workspace, 'Grid', [inGridName])[0]
spatRef = arcpy.Describe(inFC).spatialReference
segFC = completePath(workspace,'Temp',[segFCName])[0]

print (checkExistence([inFC]))
splitPolyLineIntoSegments(inFC, segFC)
#delete some fields:
cleanUpFields(segFC, getFieldNames(segFC)[:3])
#result: [u'Shape_Leng', u'width', u'type', u'name', u'osm_id']

#get centres 
centres = getCenter(segFC)
endpoints = getEndPoints(segFC, 'START')
bearing = getOrient(centres, endpoints)

#calculate profile points
prof = calcprofPoints(centres, bearing, nPoints, pDist)

#Convert calculated profile points into shapefile
createEmptyShapefile(workspace + '/Temp', profFCName, spatRef)

#Create table with field name from profFCName file(?)
populatePointShape(prof, nPoints,
                   getFieldNames(workspace + "/Temp/" + profFCName)[-1],
                   workspace + "/Temp/" + profFCName)
#Get it on dem surface
convert3D(workspace + "/Temp/" + profFCName, inGrid)

shifts = calcShiftTriples(workspace + "/Temp/" + profFCName,
                          getFieldNames(workspace + "/Temp/" + profFCName)[-1],
                          zdif)

tabularOutput(workspace + '//Output' + outTabName, shifts)