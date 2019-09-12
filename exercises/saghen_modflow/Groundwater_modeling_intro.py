#!/usr/bin/env python
# coding: utf-8

# 
#  <img src=".\figures\Title.png">
# 
# ### Outline
# * Review the big picture of GSFLOW model develpments
# * Explore HRU shapefile using Geopandas to read/write shapefiles
# * Exercise: Saghen Groundwater Model Development
# * Steady-State model vs. Transient 
# * Model input and output archiving in HRU shapefile
# 
# 
# 
# 
# 
# 

# ### Background
# At this stage, we have built the input files for the PRMS model using GSFLOW-arcpy. One of the files that are generated is the hru_param.shp file. This shapefile has most of the information we will need to build the MODFLOW model. 

# <img src=".\figures\WorkFlow.png">

# 
# 
# ### MODFLOW PACKAGES
#  <img src=".\figures\mf_packages.png">

# In[12]:


import os
import geopandas as gpd
import matplotlib.pyplot as plt
import flopy
import numpy as np
import pandas as pd
import datetime


# ### Explore HRU Shapefile Using Geopandas
# Let us upload the hru_param.shp file and look at it.

# In[13]:


hru_shp_file = r"../models_data/gis/hru_params.shp"
hru_shp = gpd.read_file(hru_shp_file)


# In[14]:


#Let us look at the attribute table and plot some information ....
hru_shp.head(5) # list the first 5 rows


# In[15]:


# Two ways to access data in Geopandas
hru_shp.HRU_TYPE
hru_shp['HRU_TYPE']


# In[16]:


# We can plot any field in the attribute table
hru_shp.plot(column='HRU_TYPE',  figsize=(12, 12))
plt.title("Active Domain")


# In[17]:


## access other values in hru shapefile
print(hru_shp.columns)


# In[18]:


# sort attribute table data so that the HRU_ID sorted as 1,2,3,...
hru_shp = hru_shp.sort_values(by=['HRU_ID'])
hru_shp.head(5)


# ### FLOPY
# 

# In[19]:


# Generate an empty flopy object. 
model_name = "saghen"   # model name
workspace = os.path.join(os.getcwd(), 'modflow')         # Work space folder
exe_file = r"..\..\bin\MODFLOW-NWT"   # The location of the executable Modflow

mf = flopy.modflow.Modflow(model_name, model_ws=workspace, exe_name=exe_file,  version='mfnwt')
print(mf)


# ### Model discretization - DIS package
# * This package define the spatial and time domain of the problem,
# * Discretize the domain using the grid used for HRU
#  <img src=".\figures\dis.png">

# In[20]:


# Define the grid -- Space descritization
n_row = hru_shp["HRU_ROW"].max()    # number of rows
n_col = hru_shp['HRU_COL'].max()    # number of cols
del_r = 90.0                        # Can you get cell size from hru_param? hru_shp.HRU_X[1] - hru_shp.HRU_X[0]?
del_c = 90.0
print(n_col, n_row)


# In[21]:


# The domain groundwater model is a 3D, so we need to specify the 
# Vertical discretization (number of layers and their elevations) 
nlayrs = 2                           # Number of the layers
thk1 = np.loadtxt(r"../models_data/misc/thickness1.txt")            # thickness of layer 1 
thk2 =  np.loadtxt(r"../models_data/misc/thickness2.txt")           # thickness of layer 2 

plt.imshow(thk2); plt.colorbar()


# In[22]:


# Layers elevation
top_elv = hru_shp["DEM_ADJ"].values.reshape(n_row, n_col)   # Ground surface elevation


botm_elvs = np.zeros((nlayrs, n_row, n_col))                # 3D array that will hold the elevation of bottoms of each layer
botm_elvs[0,:,:] = top_elv - thk1                           # bottom of layer 1
botm_elvs[1,:,:] = botm_elvs[0,:,:] - thk2                  # bottom of layer 2

# plots
f, axs = plt.subplots(2,1,figsize=(15,15))
plt.subplot(1,2,1)
btm1 = np.ma.masked_where(thk1<2.0, botm_elvs[0,:,:])
plt.imshow( btm1, cmap = 'jet'); plt.colorbar(fraction=0.046, pad=0.04); plt.title("Bottom of layer1")
plt.subplot(1,2,2)
btm2 = np.ma.masked_where(thk1<2.0, botm_elvs[1,:,:])
plt.imshow(btm2, cmap = 'jet'); plt.colorbar(fraction=0.046, pad=0.04);  plt.title("Bottom of layer2")


# ### Discretization of Simulation Period
# <img src = ".\figures\StressPeriod.png">

# In[23]:


# Simulation period & time steps -- -- Temporal discretization
start_date = datetime.date(year = 1982,month = 8,day = 1)
end_date = datetime.date(year = 1997,month = 3,day = 31)
time_span = end_date - start_date
time_span = time_span.days
nper = 2                                            # Number of stress periods
perlen = [1.0, time_span]                           # length of each stress period
nstp =   [1.0, time_span]                           # time steps in each stress period
is_steady =[ True, False]                           # First stress period is Steady-state, the second is Transient
tim_unit = 4                                        # days
len_unit = 2                                        # meters
xul = hru_shp.total_bounds[0]                       # x coordinate of upper left corner of the grid
yul = hru_shp.total_bounds[3]                       # y coordinate of upper left corner of the grid,

# Now generate the dis object. The object holds all the information about the grid and simulation time.
dis = flopy.modflow.ModflowDis(mf, nlay=nlayrs, nrow=n_row, ncol=n_col, delr=del_r, delc=del_c,top=top_elv, botm=botm_elvs, 
                                       nper=nper, perlen=perlen, nstp=nstp, steady=is_steady,  itmuni= tim_unit, 
                                       lenuni = len_unit)  

mf


# ### Important Resources
# #### Flopy Documentation
# http://modflowpy.github.io/flopydoc/
# 
# #### MODFLOW online help 
# https://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/

# In[24]:


#dis.botm.array
#dis.check()
dis.plot()


# ### BAS Package
# * Define active and inactive zones
#     * HRU_TYPE = 0 --- Inactive
#     * HRU_TYPE = 1 --- Active
#     * HRU_TYPE = 2 --- Lake
#     
# * Define the satring head in the model
# 
# <img src=".\figures\cell_types.png">

# In[25]:


## Read HRU_TYPE from hru shape file and reshape it into 2D domain
ibound2d = hru_shp["HRU_TYPE"].values.reshape(n_row, n_col)

plt.imshow(ibound2d)


# In[26]:


## Constant Head
const_head_rows = [41,42,43]
const_head_cols = [79,79,79]
ibound2d[const_head_rows, const_head_cols] = -1
plt.imshow(ibound2d)


# In[27]:


## HRU shapefile has a 2D map of the inactive zones, so we need to define the active domain for the 3D groundwater domain.
ibound3d = np.zeros((nlayrs, n_row, n_col))
for lay in range(nlayrs):
    ibound3d[lay, :,:] = ibound2d
    

ibound3d.shape


# In[28]:


## initial head
initial_head = np.zeros((nlayrs, n_row, n_col)) 

strt1 = np.loadtxt(r"../models_data/misc/initial_head1.txt")
strt2 = np.loadtxt(r"../models_data/misc/initial_head2.txt")
# strt1 = mf.dis.top.array 
# strt2 =  mf.dis.top.array 
initial_head[0,:,:] = strt1
initial_head[1,:,:] = strt2

bas = flopy.modflow.ModflowBas(mf, ibound=ibound3d, strt=initial_head)
bas.plot()


# In[ ]:





# In[29]:


# Check packages that are assigned so far...
mf.get_package_list()


# ## Ploting the Grid ....

# In[30]:


fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(1, 1, 1, aspect='equal')
modelmap = flopy.plot.ModelMap(model=mf, rotation=0.0)
quadmesh = modelmap.plot_ibound()
linecollection = modelmap.plot_grid()



# In[31]:


# cross section
fig = plt.figure(figsize=(20, 10))
col_num = 50
ax = fig.add_subplot(1, 2, 1)
modelxsect = flopy.plot.ModelCrossSection(model=mf, line={'Column': col_num})
patches = modelxsect.plot_ibound()
linecollection = modelxsect.plot_grid()
t = ax.set_title('Column{}'.format(col_num))

ax = fig.add_subplot(1, 2, 2)
row_num = 50
modelxsect = flopy.plot.ModelCrossSection(model=mf, line={'Row': row_num})
patches = modelxsect.plot_ibound()
linecollection = modelxsect.plot_grid()
plt.ylim(2600,1500)
ax.invert_yaxis()
t = ax.set_title('Row {}'.format(row_num))


# ###  Upstream Weighting package (UPW) 
# When MODFLOW-NWT is used the UPW package must be used. For other versions of MODFLOW, the LPF package can be used. 
# 
# This package is used to define the hydraulic properties of the aquifer such as:
# *  horizontal and vertical hydraulic conductivity, 
# *  storage terms such as the specific storage and specfic yield.
# *  Anistropy 
# *  Layer type (Confined, unconfined, convertable)

# In[ ]:






# In[32]:


laytyp = np.ones(nlayrs)  # convertable layer
avg_typ = 0               # 0 is harmonic mean 1 is logarithmic mean 2 is arithmetic mean 
h_anis = 1.0              # a flag or the horizontal anisotropy
layvka = 0                # 0—indicates VKA is vertical hydraulic conductivity
laywet = np.zeros(nlayrs) #contains a flag for each layer that indicates if wetting is active. 
                          #laywet should always be zero for the UPW Package 
# Hydraulic conductivity
kh = np.zeros((nlayrs, n_row, n_col))
kh[0,:,:] = np.loadtxt(r"../models_data/misc/hk1.txt")
kh[1,:,:]=np.loadtxt(r"../models_data/misc/hk2.txt")

# Specific Storage
ss = np.zeros((nlayrs, n_row, n_col))
ss[0,:,:] = np.loadtxt(r"../models_data/misc/ss1.txt")
ss[1,:,:]=np.loadtxt(r"../models_data/misc/ss2.txt")

# Specific Storage
sy = np.zeros((nlayrs, n_row, n_col))
sy[0,:,:] = np.loadtxt(r"../models_data/misc/sy1.txt")
sy[1,:,:]=np.loadtxt(r"../models_data/misc/sy1.txt")  


upw = flopy.modflow.mfupw.ModflowUpw(mf, laytyp=laytyp, layavg=avg_typ, chani=h_anis, layvka=layvka, laywet=laywet,
                                             hdry=-1e+30, iphdry=0, hk=kh, hani=1.0, vka=(kh * 0.1), ss=ss, sy=sy,
                                             vkcb=0.0, noparcheck=False, ipakcb = 55 , extension='upw')

## Can you Check UPW package? 


# In[33]:


plt.imshow(sy[1,:,:]<=0.01)


# ### Streamflow-Routing (SFR2) Package
# The package is used to simulate stream flow and the interaction between the groundwater aquifer and the stream network.
# 
# <img src = ".\figures\sfr1.png">
# 
# #### Structure of SFR input file
# 
# <img src = ".\figures\sfr2.png">
# 
# 
# 

# In[34]:


# The stream data can be extracted from the hru shapefile by masking out all cells that has ISEG value equel to 0.
mask = hru_shp['ISEG'] > 0
streams_data = hru_shp[mask] # a compact form is streams_data = hru_shp[hru_shp['ISEG'] > 0]
streams_data.plot(column = 'ISEG', cmap='Set1', figsize=(10, 8))
plt.title("Simulated stream network")
#streams_data


# #### Reach Data
# Reach Data includes information about:
# * the reaches in each segments,
# * their locations(layer, row, col),
# * reach lengths, 
# * streambed elevations and slopes,
# * streambed thickness,
# * streamd hydraulic conductivity,
# * properties of the unsaturated zone. 

# In[35]:


## Reach Data
# The reach data will be saved in a Pandas dataframe, which will make it simpler to handle the tabular data.
# Table fields name
reach_data_labels = ['node', 'k',  'i', 'j','iseg', 'ireach','rchlen', 'strtop', 'slope',
                     'strthick','strhc1', 'thts',  'thti','eps', 'uhc', 'reachID', 'outreach']
# Initialize an empty pandas dataframe
reach_data = pd.DataFrame(columns=reach_data_labels, dtype='float')

# Reach location
reach_data['k'] = streams_data['KRCH'] - 1    # layer number-- Notice that layer numbers are zero-based 
reach_data['i'] = streams_data['IRCH'] - 1    # row number
reach_data['j'] = streams_data['JRCH'] - 1    # column number
# IDs
reach_data['iseg'] = streams_data['ISEG']     # Segment ID number
reach_data['ireach'] = streams_data['IREACH'] # Reach ID number
# Stream topography
reach_data['rchlen'] = streams_data['RCHLEN']            # reach length
reach_data['strtop'] = streams_data['DEM_ADJ'] - 1.0     # Streambed elevation is assumed 1 meter below ground surface.
reach_data['slope'] = streams_data['DEM_SLP_P'] / 100.0  # Slope

# Streambed information 
reach_data['strthick'] = 0.5    # streambed thickness - meter   
reach_data['strhc1'] = 0.1      # conductivity of the stream bed

#Unsaturated Zone properties
reach_data['thts'] = 0.31      # saturated porosity
reach_data['thti'] = 0.131     # initial water content
reach_data['eps'] = 3.5        # Brooks-Corey exponent 
reach_data['uhc'] = 0.1        # conductivity of the unsaturated zone
n_reaches = len(reach_data)    # number of reaches 

# Show the first five lines in the reach data table

reach_data.head(10)


# ### Segment Data:
# This section provides information about each segments that is realted to:
# * Method to calculte stream flow inside the stream channel,
# * Define Connections of the segments with each others,
# * Inflow and ouflow from each segments,
# * Cross-section geolmetry.
# 
# <img src = ".\figures\sfr3.png">

# In[36]:


seg_data_labels = ['nseg', 'icalc', 'outseg', 'iupseg', 'iprior',
                   'nstrpts', 'flow', 'runoff', 'etsw', 'pptsw', 'roughch', 'roughbk',
                   'cdpth', 'fdpth', 'awdth', 'bwdth', 'hcond1', 'thickm1',
                   'elevup', 'width1', 'depth1', 'hcond2', 'thickm2', 'elevdn',
                   'width2', 'depth2']

# Use the stream data from the HRU shapefile
unique_segments = streams_data.drop_duplicates(['ISEG'], keep='first')
unique_segments = unique_segments.sort_values(by='ISEG')
unique_segments


# In[37]:


n_segments =  len(unique_segments)

# initialize dataframe filled with zeros
zero_data = np.zeros((n_segments, len(seg_data_labels)))
segment_data = pd.DataFrame(zero_data, columns=seg_data_labels, dtype='float')

segment_data['nseg'] = unique_segments['ISEG'].values       # Segment ID
segment_data['icalc'] = 1                                   # Use Manning's Equation for a rectangular cross-section
segment_data['outseg'] = unique_segments['OUTSEG'].values   # Downstream Segment
segment_data['iupseg'] = unique_segments['IUPSEG'].values   # segmet id for Upstream diversion or negative ID of the lake 
segment_data['width1'] = 3.0                                # Upstream width 
segment_data['width2'] = 3.0                                # Downstream width 
segment_data['roughch'] = 0.04                              # Roughness Coeffcient in Manning's Equation

segment_data


# In[38]:


## Can you think of another way to compute the widths if you have no data? 
streams_data.plot(column = 'DEM_FLOWAC')
if False:    
    max_width = 20.0
    min_width = 1.0
    flow_acc_range = streams_data['DEM_FLOWAC'].max() - streams_data['DEM_FLOWAC'].min()
    widths = min_width + (max_width - min_width)* (streams_data['DEM_FLOWAC'].values - streams_data['DEM_FLOWAC'].min())/flow_acc_range


# 

# In[ ]:





# ### SFR2 General Options

# In[39]:


## This the options in the first line in the SFR package
nsfrpar = 0    # number of parameters 
nparseg = 0
isfropt = 3
const = 86400  # constant for manning's equation, units of ??
dleak = 0.0001 # closure tolerance for stream stage computation
ipakcb = 55    # flag for writing SFR output to cell-by-cell budget (on unit 55)
istcb2 = 81    # flag for writing SFR output to text file
nstrail = 15   # used when USZ is simulated, number of trailing wave increments
isuzn = 1      # used when USZ is simulated, number of vertical cells in unz, for icalc=1, isuzn = 1
nsfrsets = 50  # used when USZ is simulated, number of sets of trailing wave
irtflg = 0     # an integer value that flags whether transient streamflow routing is active
numtim = 2     # used when irtflg > 0, number of sub time steps to route streamflow
weight = 0.75  # used when irtflg > 0,A real number equal to the time weighting factor used to calculate the change in channel storage.

# The Segments information can be changed with time
dataset_5 = {}
for i in np.arange(nper): # we have only two stress period
    if i == 0:
        tss_par = n_segments
    else:
        tss_par = -1   # the negative sign indicates that segment data from previous time step will be used
    dataset_5[i] = [tss_par, 0, 0]

# The flopy needs reach data and segment data as numpy recarray data structure
### There is a bug in flopy here.... to avoid the error sort data
reach_data = reach_data.sort_values(by=['iseg', 'ireach'])
segment_data = segment_data.sort_values(by=['nseg'])
reach_data.head(5)


# In[40]:


reach_data = reach_data.to_records(index=False)
segment_data = segment_data.to_records(index=False)
segment_data = {0: segment_data}
# you can change segments data for each stress period? segment_data = {0: segment_data0, 1: segment_data1 }

# channel flow data
channel_flow_data =     {}  # for 6e - flow table [flow1 flow2; depth1, depth2, width1, width2]
channel_geometry_data = {}  # 6d - complex channel cross-section

sfr = flopy.modflow.ModflowSfr2(mf, nstrm=n_reaches, nss=n_segments, const=const, nsfrpar= nsfrpar, nparseg = nparseg,
                                        dleak=dleak, ipakcb=ipakcb, nstrail = nstrail, isuzn = isuzn,  nsfrsets= nsfrsets,
                                        istcb2=istcb2, reachinput=True, isfropt = isfropt, irtflg = irtflg,
                                        reach_data=reach_data, numtim = numtim, weight = weight,
                                        segment_data=segment_data,
                                        channel_geometry_data=channel_geometry_data,
                                        channel_flow_data=channel_flow_data,
                                        dataset_5=dataset_5)
mf.get_package_list()


# In[41]:


sfr.plot()


# ### Output Control Package
# This is where we tell MODFLOW how to print results output. It is wise to print the results only at the time you are interseted in. 

# In[42]:


# Add OC package to the MODFLOW model
options = ['PRINT HEAD', 'PRINT DRAWDOWN', 'PRINT BUDGET',
           'SAVE HEAD', 'SAVE DRAWDOWN', 'SAVE BUDGET',
         'SAVE IBOUND', 'DDREFERENCE']

# nstp =   [1.0, 5844.0]
spd = dict()  
steps_to_print = np.linspace(0,nstp[1]-1, 500).astype(int)
key = (0, 0)
spd[key] = ['SAVE HEAD', 'PRINT BUDGET', 'SAVE BUDGET' ]  

for time_point in steps_to_print:
    key = (1,time_point)
    spd[key] = ['SAVE HEAD', 'PRINT BUDGET', 'SAVE BUDGET' ] 

spd


# In[43]:


oc = flopy.modflow.ModflowOc(mf, stress_period_data=spd, cboufm='(20i5)')
mf.get_package_list()


# In[ ]:





# ### Unsaturated Zone Flow (UZF) Package
# The Unsarurated Zone (USZ) plays a major role in underatanding the interaction between deep groundwater system ans surface water system. 

# In[44]:


nuztop =  3         # Recharge to and discharge from the top model layer
iuzfopt = 1         # Vertical conductivity will specifed from upw
irunflg = 2         # >0 means water discharge will be routed to the streams.
ietflg = 0          # > 0 ET will be simulated
ipakcb = 70         # > 0 recharge, ET, and discharge will be written unformatted file
#iuzfcb2 = -132      # > 0  recharge, ET, and ground-water discharge to land surface rates to a separate unformatted file
ntrail2 = 15        # number of trailing waves
nsets = 100          # number of wave sets used to simulate multiple infiltration periods
nuzgag = 0          # equal to the number of cells (one per vertical column) that will be specified for printing
                    # detailed information on the unsaturated zone water budget and water content.
surfdep = 1.0       # The average height of undulations, D (Figure 1 in UZF documentation), in the land surface altitude

iuzfbnd = ibound2d  # used to define the aerial extent of the active model in which recharge and discharge will be simulated.
irunbnd = hru_shp['IRUNBOUND'].values.reshape(n_row, n_col)
plt.figure(figsize=(10,10))
plt.imshow(irunbnd)


# In[45]:


finf = np.loadtxt(r"../models_data/misc/uzf_finf.txt")

## If you know that infiltration is a fraction (say 20%) of the annual rain, can you use information from the HRU
##  shapefile to compute finf?

# **** Answer ****
annual_rain = 0.0
for ii in np.arange(1, 13):
    #curr_ = np.copy(zmat)
    field_name = 'PPT_' + str(ii).zfill(2)
    annual_rain = annual_rain + hru_shp[field_name].values
annual_rain = 0.20 *  (annual_rain/ 365.25)/1000.0   # convert units from mm/year to m/day




# In[46]:


#uzf.plot()
plt.imshow(annual_rain.reshape(n_row, n_col)); plt.colorbar()


# In[47]:


thts = np.loadtxt(r"../models_data/misc//uzf_ths.txt") # porosity of the unsaturated zone
vks = np.loadtxt(r"../models_data/misc//uzf_vks.txt") # vertical hydraulic conductivity
thetai = 0.2  # initial moisture content.

uzf = flopy.modflow.ModflowUzf1(mf, nuztop=nuztop, iuzfopt=iuzfopt, irunflg=irunflg, ietflg=ietflg,
                                ipakcb=ipakcb, iuzfcb2=0, ntrail2=ntrail2, nsets=nsets, 
                                surfdep=surfdep, iuzfbnd=iuzfbnd, irunbnd=irunbnd, vks=vks,
                                eps=4.0, thts= thts, thti=thetai, specifythtr=0, specifythti=0, nosurfleak=0,
                                finf=finf)


# In[48]:


#uzf.write_file()


# In[49]:


mf.get_package_list()


# ### NWT Solver

# In[50]:


flopy.modflow.mfnwt.ModflowNwt.load(r"../models_data/misc/solver_options.nwt", mf)
if False:
    nwt = flopy.modflow.mfnwt.ModflowNwt(mf, headtol=0.01, fluxtol=500, maxiterout=1000, thickfact=1e-06, linmeth=2,
                                           iprnwt=1, ibotav=1, options='SPECIFIED', Continue=True, dbdtheta=0.4,
                                           dbdkappa=1e-05, dbdgamma=0.0, momfact=0.1, backflag=1, maxbackiter=50,
                                           backtol=1.1, backreduce=0.7, maxitinner=50, ilumethod=2, levfill=5,
                                           stoptol=1e-10, msdr=15, iacl=2, norder=1, level=5, north=7, iredsys=0,
                                           rrctols=0.0, idroptol=1, epsrn=0.0001, hclosexmd=0.0001, mxiterxmd=50,
                                           extension='nwt', unitnumber=None, filenames=None)


# In[51]:


mf.get_package_list()


# In[52]:


mf.write_input()


# In[53]:


mf.run_model()


# ### Learn more About Flopy !!
# https://github.com/modflowpy/flopy/tree/develop/examples/Notebooks

# In[54]:


get_ipython().system(u'jupyter nbconvert --to script Groundwater_modeling_intro.ipynb')


# In[ ]:





# In[ ]:




