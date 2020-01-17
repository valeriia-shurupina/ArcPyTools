'''
    Calculation of overlap between a set of polygon shapes,
    overlaping polygons will be calculated and stored

    Coding for Python 3.7
    Version: Jan, 10
'''
# imports
import os
import arcpy

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

#join project dirctory, subdirs and file names into complete paths
        
def completePath (workspace,subdir, nameList):
    for ix in range (len(nameList)):
        nameList[ix] = workspace + '/' + subdir + '/' +nameList[ix]
    return nameList 
    
#check whether a file exists under the given path
def checkExistence(pathList): #path to file 
    check=True #boolean value
    for data in pathList:
        if not arcpy.Exists (data):
            check=False 
            print ('! dataset'+ data + 'is missing')
            break #dont want to check the others if something is missing
    return check

#shapefile
def getFieldNames (table):
    fnames =[]
    fields =arcpy.ListFields(table)
    if fields: 
        for field in fields:
            fnames.append(field.name)
    return fnames

#remove some fields by specifying the names you want to keep
def cleanupFields (table, keepFields):
    delFields=list (set (getFieldNames(table) [2:]) -
                    set(keepFields) )
    arcpy.DeleteField_management (table,delFields)
    
#produces a polygon union
def generateUnion(inFCs, outFC):
    arcpy.Union_analysis(inFCs, outFC, 'ONLY_FID')

#add field to store the results of overlap detection
def addConflictField(inFC, fname, ftype):
    arcpy.AddField_management(inFC, fname, "TEXT")

#find overlaps from analysis of the original feature IDs (FIDs)
def findOverlaps(inFC, fieldList):
    cursor = arcpy.UpdateCursor(inFC, fieldList)
    nfields = len(fieldList)
    
    for row in cursor:
        code = ""
        for ix in range(nfields-1):
            if row.getValue(fieldList[ix]) >= 0:
                code = code + '_' + str(ix)
        if code.count('_') == 1:
            code = 'ok'
        row.setValue(fieldList[-1], code)
        cursor.updateRow(row)
            
    del cursor
        
#
def deleteNonConflict(inFC):
    arcpy.MakeFeatureLayer_management(inFC, "tempLayer")
    whereClause = ' "CONFLICT" = \'ok\' '
    arcpy.SelectLayerByAttribute_management("tempLayer", "NEW_SELECTION", 
                                            whereClause)
    arcpy.DeleteFeatures_management("tempLayer")

################################################################        

arcpy.env.overwriteOutput=True

workspace='C:/Users/User/YandexDisk/Studying/TUD/GIS-Applications-Python/Tool-2-Overlap'
subdirList=['Temp','Shape','Output']
#createSubdir(workspace,subdirList)
inFCNames=['Building.shp', 'Green.shp', 'Traffic.shp', 'Street.shp', 'Sealed.shp']  #list of files this is why []
outFCNames='overlap.shp'

createSubdir(workspace,subdirList)
for ix, name in enumerate(inFCNames):
    inFCNames[ix] = controlExtension(name, '.shp')

inFCs=completePath (workspace, 'Shape', inFCNames)
outFC = completePath (workspace, 'Output', [outFCNames])[0]
print(checkExistence(inFCs))
generateUnion(inFCs, outFC)
addConflictField(outFC, "CONFLICT", "TEXT")
findOverlaps(outFC, (getFieldNames(outFC)[2:]))
deleteNonConflict(outFC)