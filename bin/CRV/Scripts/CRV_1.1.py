#-------------------------------------------------------------------------------
# Name:        CRV_1.1.py
# Purpose:     Create lines representing cascades based on flow and symbolize 
#              cascade features including several types of swale and streams or 
#              outflow points 
#
# Author:      cjmayers@usgs.gov; rlmedina@usgs.gov
#
# Created:     08/09/2011
# Updated:     04/23/2015
#-------------------------------------------------------------------------------

'''
The U.S. Geological Survey CRT is a standalone computer application for hydrologic models,
including the Coupled Groundwater Surface-Water Flow Model (GSFLOW), and Precipitation-Runoff 
Modeling System (PRMS). The Cascade Routing Visualization (CRV) tool takes the standalone CRT's output 
and creates 2 feature classes (CascadeFlow, CascadeType) in a file-based geodatabase 
(CRV.gdb) to visualize flow between cells (cascades) and various cascade features 
including several types of swale and streams or outflow points. The tool calls and executes 
the standalone CRT executable to generate the necessary VIS.TXT file. Alternatively, a valid 
VIS.TXT file can be provided as input for the tool.
'''

import sys
import os
import subprocess
import arcpy
import traceback
import shutil

# CRT.exe failed to generate cascades
class CRTfail(Exception):
    pass

# Missing CRT executable file exception
class MissingCRTexe(Exception):
    pass

# Missing or empty CRT output file exception
class MissingCRTfile(Exception):
    pass

# Missing CRT input file exception
class MissingInputFile(Exception):
    pass

# Missing VISFLG flag
class MissingVISFLG(Exception):
    pass

# Missing Arc product exception
class NoProduct(Exception):
    pass

# Reserved name found in Map documents table of contents
class ReservedName(Exception):
    pass

txt = '...CRV.py...'
arcpy.AddMessage(txt + '\n')

# User defined variables; from ArcMap session
userWorkspace = arcpy.GetParameterAsText(0) # User defined workspace
visulizationOnly = arcpy.GetParameterAsText(1) # Visulization Only; requires a valid vis.txt file in the user workspace 
if visulizationOnly == 'true':
    visulizationOnly = True
else:
    visulizationOnly = False

# Body of code
try:
    # Check ArcGIS Product
    txt = 'Checking ArcGIS product level...'
    arcpy.AddMessage(txt)    
    ARCproducts = ['ArcInfo', 'ArcEditor']
    ARCproductValues = ['Available','AlreadyInitialized']
    ARCproductFlag = False
    for ARCproduct in ARCproducts:
        if arcpy.CheckProduct(ARCproduct) in ARCproductValues:
            ARCproductFlag = True
    if ARCproductFlag == False:
        raise NoProduct
    arcpy.env.overwriteOutput = True        
    
    # Check that all required input files are present
    txt = 'Checking for required input files and visualization flags...'
    arcpy.AddMessage(txt)  
    workspaceFiles = os.listdir(userWorkspace)   
    if visulizationOnly:
        txt = '\'Visulization Only\' option selected; using an existing vis.txt file; FLOWFLG assumed to be 0...'
        arcpy.AddMessage(txt)          
        requiredInputFiles = ['vis.txt']
        requiredCRTFiles = []
        CASC_PCT_Flag = True # flag - check for percent flows of either 66 or 75%
        FLOWFLG = 0 # defaults value; assumes 4 flow percentage bins 
    else:
        CASC_PCT_Flag = False # flag - don't check for percent flows... FLOWFLG set explicitly
        requiredInputFiles = ['HRU_CASC.DAT','LAND_ELEV.DAT','STREAM_CELLS.DAT'] 
        # Check for user designated optional files
        if 'HRU_CASC.DAT' in workspaceFiles:
            HRU_CASC_file = userWorkspace +'\\' + 'HRU_CASC.DAT'
            with open(HRU_CASC_file, 'r') as f:
                for line in f:
                    data = line.strip('\n').split()
                    if 'HRUFLG' in data:
                        HRUFLG = int(data[0])
                        STRMFLG = int(data[1])
                        FLOWFLG = int(data[2]) #used to select correct CascadeFlow representation
                        VISFLG = int(data[3])
                        if VISFLG != 1:
                            raise MissingVISFLG
                        for fileFlag, value, fileName in ((HRUFLG, 1, 'HRU_ID.DAT'), (STRMFLG, 0, 'OUTFLOW_HRU.DAT'), (VISFLG, 1, 'XY.DAT')):
                            if fileFlag == value:
                                requiredInputFiles.append(fileName)
                        break
    for workspaceFile in workspaceFiles:
        index = workspaceFiles.index(workspaceFile)
        workspaceFiles[index] = workspaceFile.upper()
    missingFiles = []
    for rFile in requiredInputFiles:
        if rFile.upper() not in workspaceFiles:
            missingFiles.append(rFile)
        elif os.path.getsize(userWorkspace +'\\'+ rFile) == 0:
            missingFiles.append(rFile)            
    if missingFiles != []:
        raise MissingInputFile
    
    # Script location
    scriptLoc = os.path.dirname(sys.argv[0])
    
    # Run CRT executable to create new vis.txt file
    if not visulizationOnly:
        # Call CRT.exe process to generate cascades
        txt = 'Calling CRT.exe to generate vis.txt..'
        arcpy.AddMessage(txt)
        program = scriptLoc.split('\\')[:-2]
        program.extend(['BIN','CRT_1.3.1.exe'])
        program = '\\'.join(program)
        if not os.path.exists(program):
            raise MissingCRTexe 
        programLocation = userWorkspace
        CRT = subprocess.Popen([program], stdout=subprocess.PIPE, cwd=programLocation)        
        out, err = CRT.communicate()
        txtlines = out.split('\n')
        for txt in txtlines:
            arcpy.AddMessage(txt[:-1])
        if ' CASCADES SUCCESSFULLY GENERATED.\r' not in txtlines:
            raise CRTfail
                        
        # Check for CRT output files
        txt = 'Checking for CRT output files...'
        arcpy.AddMessage(txt)     
        requiredCRTFiles = ['casc_pct.out', 'hru_down_id.out', 'hru_strmseg_down_id.out',
                            'hru_up_id.out', 'cascade.param', 'groundwater_cascade.param',
                            'outputstat.txt', 'parameter_dimensions.txt', 'vis.txt']
        workspaceFiles = os.listdir(userWorkspace)
        for workspaceFile in workspaceFiles:
            index = workspaceFiles.index(workspaceFile)
            workspaceFiles[index] = workspaceFile.lower()
        missingFiles = []
        for rFile in requiredCRTFiles:
            if rFile not in workspaceFiles:
                missingFiles.append(rFile)
            elif os.path.getsize(userWorkspace +'\\'+ rFile) == 0:
                missingFiles.append(rFile)
        if missingFiles != []:
            raise MissingCRTfile        
        
    # Set variables; all included as part of tool share
    inFile = userWorkspace +'\\'+ 'vis.txt'
    
    toolWorkspace = os.path.split(scriptLoc)[0]
    toolDataWorkspace = toolWorkspace +'\\'+ 'ToolData'
    
    toolGDBloc = toolDataWorkspace
    toolGDBname = 'CRVTemplate.gdb'
    toolGDB = toolGDBloc +'\\'+ toolGDBname

    cascadeFlowTemplateFCloc = toolGDB     
    cascadeFlowTemplateFCname = 'CascadeFlow_XX'  
    cascadeFlowTemplateFC = cascadeFlowTemplateFCloc +'\\'+ cascadeFlowTemplateFCname   
    
    cascadeTypeTemplateFCloc = toolGDB     
    cascadeTypeTemplateFCname = 'CascadeType_XX'  
    cascadeTypeTemplateFC = cascadeTypeTemplateFCloc +'\\'+ cascadeTypeTemplateFCname       
    
    # Set variables; all based on user workspace and open map document
    mxd = arcpy.mapping.MapDocument('CURRENT')
    df = arcpy.mapping.ListDataFrames(mxd)[0] 
    mapLayers = arcpy.mapping.ListLayers(mxd, 'Cascade*', df) # Find pre-exisiting 'CRV Output' in map document
    mapCounters = []
    for mapLayer in mapLayers:
        if mapLayer.name in ['CascadeFlow_XX', 'CascadeType_XX']:
            raise ReservedName
        try:
            mapCounter = int(mapLayer.name.split(' ')[-1])
            if mapCounter not in mapCounters:
                mapCounters.append(mapCounter)
        except:
            pass
    outGDBloc = userWorkspace +'\\'+ 'CRV_1'    
    counter = 1
    while os.path.isdir(outGDBloc) or counter in mapCounters: # Increment folder name; find unquie name
        dirHead = os.path.split(outGDBloc)[0]
        dirTail = os.path.split(outGDBloc)[1]
        numberStart = dirTail.find('_') + 1
        counter = int(dirTail[numberStart:])
        counter += 1
        outGDBloc = dirHead +'\\'+ dirTail[:numberStart] + str(counter)
    os.mkdir(outGDBloc)
        
    counter = '_' + str(counter)        
    outGDBname = 'CRV' + counter + '.gdb'
    outGDB = outGDBloc +'\\'+ outGDBname
    
    cascadeFlowFCloc = outGDB 
    cascadeFlowFCname = 'CascadeFlowPercent' + counter 
    cascadeFlowFC = cascadeFlowFCloc +'\\'+ cascadeFlowFCname 

    cascadeTypeFCloc = outGDB 
    cascadeTypeFCname = 'CascadeType' + counter 
    cascadeTypeFC = cascadeTypeFCloc +'\\'+ cascadeTypeFCname 

    # Setup output group in map document for script results
    outputGroup = 'CRV Output'
    outputGroupLayerFile = toolDataWorkspace +'\\'+ 'CRVOutput.lyr'
    outputGroupLayers = arcpy.mapping.ListLayers(mxd, 'CRV Output', df)
    if len(outputGroupLayers) == 0:
        txt = 'Adding \'{0}\' group to the open map document...'.format(outputGroup)
        arcpy.AddMessage(txt)
        arcpy.mapping.AddLayer(df, arcpy.mapping.Layer(outputGroupLayerFile), 'TOP')    
    else:
        txt = '\'{0}\' group found in the open map document...toggling off previous output...'.format(outputGroup)
        arcpy.AddMessage(txt)
        TOClayers = arcpy.mapping.ListLayers(mxd,'', df)
        for TOClayer in TOClayers:
            if outputGroup in TOClayer.longName and outputGroup != TOClayer.longName:
                TOClayer.visible = False
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
    inGroupLayer = arcpy.mapping.ListLayers(mxd,outputGroup, df)[0]
    
    # Create a new file-based geodatabase
    txt = 'Creating a new file-based geodatabase ({0})...'.format(outGDBname)
    arcpy.AddMessage(txt)
    arcpy.CreateFileGDB_management(outGDBloc, outGDBname)
    
    # Create cascade-flow feature class and add fields.
    txt = 'Creating a cascade-flow feature class and adding fields...'
    arcpy.AddMessage(txt)
    arcpy.CreateFeatureclass_management(cascadeFlowFCloc, cascadeFlowFCname, 'POLYLINE', '#', 'DISABLED', 'DISABLED')
    fieldInfo = [('CASCADE_ID', 'LONG'),('HRU_UP_ID', 'LONG'),('CASCADE_TYPE_UP', 'LONG'),('UP_ROW', 'LONG'),
                 ('UP_COL', 'LONG'),('UP_X', 'DOUBLE'),('UP_Y', 'DOUBLE'),('HRU_DOWN_ID', 'LONG'), 
                 ('CASCADE_TYPE_DOWN', 'LONG'),('DOWN_ROW', 'LONG'),('DOWN_COL', 'LONG'),('DOWN_X', 'DOUBLE'),
                 ('DOWN_Y', 'DOUBLE'),('CASC_PCT', 'DOUBLE'),('HRU_STRM_SEG_DOWN', 'LONG')]
    for field, fType in fieldInfo:
        arcpy.AddField_management(cascadeFlowFC, field, fType)
    
    # Open a cursor to insert rows into the shapefile; Create Array and Point objects
    cur = arcpy.InsertCursor(cascadeFlowFC)
    lineArray = arcpy.CreateObject('Array')
    pnt = arcpy.CreateObject('Point')
    
    hruInfo = {} # Store HRU cascade info to locate swales
    
    # Open and process input file
    txt = 'Processing input file and updating cascade feature class...'
    arcpy.AddMessage(txt)
    with open(inFile, 'r') as f:
        headerFlag = True
        for line in f:
            data = line.strip('\n').split(',')
            if headerFlag: # Process header line
                fieldIndex = {}
                fieldList = []
                for field in data:
                    field = field.strip()
                    fieldList.append(field)
                    indexLoc = len(fieldList) - 1
                    fieldIndex[field] = indexLoc            
                headerFlag = False
            elif len(data) < 5: # Check for empty line
                txt = '...empty line found'
                arcpy.AddMessage(txt)
            else: # Process body of file 
                # Collect HRU info to help find unintended swales
                hruUPid = int(data[fieldIndex['HRU_UP_ID']])
                cascUPtype = int(data[fieldIndex['CASCADE_TYPE_UP']])
                hruUProw = int(data[fieldIndex['UP_ROW']])
                hruUPcol = int(data[fieldIndex['UP_COL']])
                hruUPx = float(data[fieldIndex['UP_X']])
                hruUPy = float(data[fieldIndex['UP_Y']])
                hruDOWNid = int(data[fieldIndex['HRU_DOWN_ID']])
                cascDOWNtype = int(data[fieldIndex['CASCADE_TYPE_DOWN']])
                hruDOWNrow = int(data[fieldIndex['DOWN_ROW']])   
                hruDOWNcol = int(data[fieldIndex['DOWN_COL']])
                hruDOWNx = float(data[fieldIndex['DOWN_X']])
                hruDOWNy = float(data[fieldIndex['DOWN_Y']])
                for hruID, cascType, r, c, xLoc, yLoc in [(hruUPid,cascUPtype,hruUProw,hruUPcol,hruUPx,hruUPy),
                                                          (hruDOWNid,cascDOWNtype,hruDOWNrow,hruDOWNcol,hruDOWNx,hruDOWNy)]:
                    if not hruInfo.has_key(hruID):
                        hruInfo[hruID] = {}
                        hruInfo[hruID]['TYPE'] = cascType
                        hruInfo[hruID]['ROW'] = r
                        hruInfo[hruID]['COL'] = c
                        hruInfo[hruID]['X'] = xLoc
                        hruInfo[hruID]['Y'] = yLoc
                        hruInfo[hruID]['UP'] = [] # List to collect HRU IDs that come into this HRU
                        hruInfo[hruID]['DOWN'] = [] # List to collect HRU IDs that leave this HRU
                hruInfo[hruUPid]['DOWN'].append(hruDOWNid)
                hruInfo[hruDOWNid]['UP'].append(hruUPid)                
                # Set and add X and Y coordinates of line
                pnt.X = hruUPx
                pnt.Y = hruUPy
                lineArray.add(pnt)
                pnt.X = hruDOWNx
                pnt.Y = hruDOWNy
                lineArray.add(pnt)      
                # Set the geometry feature object to the array of points and assign attirubutes
                feat = cur.newRow() # Create a feature object
                feat.shape = lineArray
                feat.CASCADE_ID = int(data[fieldIndex['CASCADE_ID']])
                feat.HRU_UP_ID = hruUPid
                feat.CASCADE_TYPE_UP = cascUPtype
                feat.UP_ROW = hruUProw
                feat.UP_COL = hruUPcol
                feat.UP_X = hruUPx
                feat.UP_Y = hruUPy
                feat.HRU_DOWN_ID = hruDOWNid
                feat.CASCADE_TYPE_DOWN = cascDOWNtype
                feat.DOWN_ROW = hruDOWNrow
                feat.DOWN_COL = hruDOWNcol
                feat.DOWN_X = hruDOWNx
                feat.DOWN_Y = hruDOWNy
                
                pct = float(data[fieldIndex['CASC_PCT']])
                check=0.
                if 0 < pct <= 0.29:
                    feat.CASC_PCT = 0.25
                elif 0.29 < pct <= 0.415:
                    feat.CASC_PCT = 0.33
                elif 0.415 < pct <= 0.58:
                    feat.CASC_PCT = 0.5
                elif 0.58 < pct <= 0.705:
                    feat.CASC_PCT = 0.66
                    check = 0.66
                elif 0.705 < pct <= 0.875:
                    feat.CASC_PCT = 0.75
                    check = 0.75
                else:    
                    feat.CASC_PCT = 1.0
                    
                feat.HRU_STRM_SEG_DOWN = int(data[fieldIndex['HRU_STRM_SEG_DOWN']])                    
                cur.insertRow(feat) # Insert the feature      
                lineArray.removeAll()
                # Test flow percent if script is executed in 'Visulization Only' mode
                if CASC_PCT_Flag:
                    if check in [.66, .75]:
                        CASC_PCT_Flag = False
                        FLOWFLG = 1
                        txt = '\'Visulization Only\' option selected; flow of 66% or 75% found... setting FLOWFLG to 1...'
                        arcpy.AddMessage(txt)                          
        try:
            # Delete pnt, lineArray, feat and cur objects to remove locks on the data
            del pnt
            del lineArray
            del feat
            del cur 
        except:
            pass
    
    # Set input variables for creating cartographic representations; Execute Add Representation
    txt = 'Execute Add Representation ({0})...'.format(cascadeFlowFCname)
    arcpy.AddMessage(txt)
    arcpy.env.workspace = toolGDB
    cascadeFlowTemplate_lyr = 'cascadeFlowTemplate_lyr1'
    arcpy.MakeFeatureLayer_management(cascadeFlowTemplateFCname, cascadeFlowTemplate_lyr)
    if FLOWFLG == 0:
        repName = 'FLOWFLG_0' 
        ruleField = 'RuleID_FLOWFLG_0' 
        overrideField = 'Override_FLOWFLG_0' 
        pctRule = [(.25,'25'),(.33,'33'),(.5,'50'),(1,'100')] 
    else:
        repName = 'FLOWFLG_1' 
        ruleField = 'RuleID_FLOWFLG_1' 
        overrideField = 'Override_FLOWFLG_1'      
        pctRule = [(.25,'25'),(.33,'33'),(.5,'50'),(.66,'66'),(.75,'75'),(1,'100')] 
        
    arcpy.SetLayerRepresentation_cartography(cascadeFlowTemplate_lyr, repName)
    editingOption = 'STORE_CHANGE_AS_OVERRIDE'
    assignOption = 'NO_ASSIGN'
    arcpy.AddRepresentation_cartography(cascadeFlowFC, repName, ruleField, overrideField, editingOption, cascadeFlowTemplate_lyr, assignOption)
    
    # Execute Calculate Representation Rule for each flow percentage rule
    txt = 'Execute Calculate Representation Rule for each flow percentage rule ({0})...'.format(cascadeFlowFCname)
    arcpy.AddMessage(txt)
    arcpy.env.workspace = outGDB 
    tempCascadeFlow_lyr = cascadeFlowFCname[:7] +' '+ cascadeFlowFCname[7:11] +' '+ cascadeFlowFCname[11:18] +' '+ cascadeFlowFCname[19:] 
    arcpy.MakeFeatureLayer_management(cascadeFlowFCname, tempCascadeFlow_lyr)
    for pct, rule in pctRule:
        expression = '\"CASC_PCT\" = ' + str(pct)
        arcpy.SelectLayerByAttribute_management(tempCascadeFlow_lyr, 'NEW_SELECTION', str(expression))
        arcpy.CalculateRepresentationRule_cartography(tempCascadeFlow_lyr, repName, rule)
    arcpy.SelectLayerByAttribute_management(tempCascadeFlow_lyr, 'CLEAR_SELECTION')
    
    # Add cascade-flow feature class to open map document 
    txt = 'Adding cascade-flow feature class to map document...'
    arcpy.AddMessage(txt)
    tempLayerFile = outGDBloc +'\\'+ cascadeFlowFCname + '.lyr'
    arcpy.SaveToLayerFile_management(tempCascadeFlow_lyr, tempLayerFile)
    arcpy.mapping.AddLayerToGroup(df, inGroupLayer, arcpy.mapping.Layer(tempLayerFile), 'TOP')       
    
    # Check for swales and streams in hruInfo
    cascadeFeatures = []
    for hru in hruInfo.keys():
        if hruInfo[hru]['TYPE'] in [2,3,4] or hruInfo[hru]['DOWN'] == []:
            cascadeFeatures.append(hru)
    
    if cascadeFeatures:
        # Create cascade-type feature class and add fields.
        txt = 'Creating cascade-type feature class and adding fields...'
        arcpy.AddMessage(txt)
        arcpy.CreateFeatureclass_management(cascadeTypeFCloc, cascadeTypeFCname, 'POINT', '#', 'DISABLED', 'DISABLED')
        fieldInfo = [('HRU_ID', 'LONG'),('CASCADE_TYPE', 'LONG'),('ROW', 'LONG'),('COL', 'LONG'),('X', 'DOUBLE'),('Y', 'DOUBLE')]
        for field, fType in fieldInfo:
            arcpy.AddField_management(cascadeTypeFC, field, fType)
        # Open a cursor to insert rows into the shapefile; Create Point object
        cur = arcpy.InsertCursor(cascadeTypeFC)
        pnt = arcpy.CreateObject('Point')         
        for hruID in cascadeFeatures:
            # Set and add X and Y coordinates of point
            hruX = hruInfo[hruID]['X']
            hruY = hruInfo[hruID]['Y']
            pnt.X = hruX
            pnt.Y = hruY        
            # Set the geometry feature object to the array of points and assign attirubutes
            feat = cur.newRow() # Create a feature object
            feat.shape = pnt
            feat.HRU_ID = hruID
            feat.CASCADE_TYPE = hruInfo[hruID]['TYPE']
            feat.ROW = hruInfo[hruID]['ROW']
            feat.COL = hruInfo[hruID]['COL']
            feat.X = hruX
            feat.Y = hruY               
            cur.insertRow(feat) # Insert the feature           
        try:
            # Delete pnt, feat and cur objects to remove locks on the data
            del pnt
            del feat
            del cur 
        except:
            pass
    
        # Find unintended swales and update CASCADE_TYPE   
        whereClause = '"CASCADE_TYPE" = 1'
        field = 'CASCADE_TYPE'
        rows = arcpy.UpdateCursor(cascadeTypeFC, whereClause, '', field)
        for row in rows:
            row.CASCADE_TYPE = 5
            rows.updateRow(row)
        try:
            # Delete row, rows objects to remove locks on the data; if rows is empty ro will not exsist
            del rows 
            del row
        except:
            pass

        # Set input variables for creating cartographic representations; Execute Add Representation
        txt = 'Execute Add Representation ({0})...'.format(cascadeTypeFCname)
        arcpy.AddMessage(txt)
        arcpy.env.workspace = toolGDB
        cascadeTypeTemplate_lyr = 'cascadeTypeTemplate_lyr'
        arcpy.MakeFeatureLayer_management(cascadeTypeTemplateFCname, cascadeTypeTemplate_lyr)
        repName = 'CascadeType' 
        arcpy.SetLayerRepresentation_cartography(cascadeTypeTemplate_lyr, repName)
        ruleField = 'RuleID_CascadeType' 
        overrideField = 'Override_CascadeType' 
        editingOption = 'STORE_CHANGE_AS_OVERRIDE'
        assignOption = 'NO_ASSIGN'
        arcpy.AddRepresentation_cartography(cascadeTypeFC, repName, ruleField, overrideField, editingOption, cascadeTypeTemplate_lyr, assignOption)
        
        # Execute Calculate Representation Rule for each flow percentage rule
        txt = 'Execute Calculate Representation Rule for each flow percentage rule ({0})...'.format(cascadeTypeFCname)
        arcpy.AddMessage(txt)
        arcpy.env.workspace = outGDB
        tempCascadeType_lyr = cascadeTypeFCname[:7] +' '+ cascadeTypeFCname[7:11] +' '+ cascadeTypeFCname[12:] 
        arcpy.MakeFeatureLayer_management(cascadeTypeFCname, tempCascadeType_lyr)
        for cascType, rule in [(2,'Lake (cascade type 2)'), (3, 'Declared swale (cascade type 3)'), 
                              (4,'Stream or outflow HRU (cascade type 4)'), (5,'Undeclared swale (cascade type 5)')]:
            expression = '\"CASCADE_TYPE\" = ' + str(cascType)
            arcpy.SelectLayerByAttribute_management(tempCascadeType_lyr, 'NEW_SELECTION', str(expression))
            arcpy.CalculateRepresentationRule_cartography(tempCascadeType_lyr, repName, rule)
        arcpy.SelectLayerByAttribute_management(tempCascadeType_lyr, 'CLEAR_SELECTION')            

        # Add cascade-type feature class to open map document 
        txt = 'Adding cascade-type feature class to map document...'
        arcpy.AddMessage(txt)
        tempLayerFile = outGDBloc +'\\'+ cascadeTypeFCname + '.lyr'
        arcpy.SaveToLayerFile_management(tempCascadeType_lyr, tempLayerFile)  
        arcpy.mapping.AddLayerToGroup(df, inGroupLayer, arcpy.mapping.Layer(tempLayerFile), 'TOP')         
    else:
        txt = 'No swales, or stream features in this dataset...'
        arcpy.AddMessage(txt)
             
    # Copying all text files to Cascade## folder (CRT input and output files)
    if visulizationOnly:
        txt = 'Copying vis.txt to {0} folder...'.format(outGDBloc)
    else:
        txt = 'Copying all text files to {0} folder (CRT input and output files)...'.format(outGDBloc)
    arcpy.AddMessage(txt)
    for requiredFiles in [requiredInputFiles,requiredCRTFiles]:                         
        for fileName in requiredFiles:
            shutil.copy(userWorkspace +'\\'+ fileName, outGDBloc +'\\'+ fileName)
   
    arcpy.AddMessage('...DONE\n')


except CRTfail:
    arcpy.AddError('CRT failed to generate cascades successfully. Review the outputstat.txt file.')   

except MissingCRTexe:
    txt = 'The CRT executable file is missing: \n...{0}'.format(program)
    arcpy.AddError(txt)

except MissingCRTfile:
    if len(missingFiles) == 1:
        txt = 'The following CRT output file is missing or invalid in the user workspace: \n...{0}'.format(missingFiles[0])
    else:
        txt = 'The following CRT output files are missing or invalid in the user workspace:'
        for mFile in missingFiles:
            txt += '\n...{0}'.format(mFile)
    arcpy.AddError(txt)

except MissingInputFile:
    if len(missingFiles) == 1:
        txt = 'The following input file is missing or invalid in the user workspace: \n...{0}'.format(missingFiles[0])
    else:
        txt = 'The following input files are missing or invalid in the user workspace:'
        for mFile in missingFiles:
            txt += '\n...{0}'.format(mFile)
    arcpy.AddError(txt)

except MissingVISFLG:   
    txt = 'In HRU_CASC.DAT file VISFLG must equal 1 for CRT.exe to generate valid vis.txt file; CRV requires the vis.txt file.... '
    arcpy.AddError(txt)

except NoProduct:   
    txt = 'Unable to find a necessary ArcGIS product ({0} or {1}); make sure you have one of these products installed...'.format(ARCproducts[0],ARCproducts[1])
    arcpy.AddError(txt)

except ReservedName:
    arcpy.AddError('Reserved name found in map document\'s table of contents (CascadeFlow_XX and/or CascadeType_XX); remove layer(s) or change layer(s) name(s) and re-run script')   

except:    
    tb = sys.exc_info()[2]    
    tbinfo = traceback.format_tb(tb)[0]    
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n"
    msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"    
    arcpy.AddError(msgs)    
    arcpy.AddError(pymsg)    
    arcpy.AddMessage(arcpy.GetMessages(1))