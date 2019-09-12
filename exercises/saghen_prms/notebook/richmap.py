#!/usr/bin/env python
# coding: utf-8

# ### Setup the Notebook Environment and Import Flopy
# Load a few standard libraries, and then load flopy.

# In[1]:


get_ipython().magic(u'matplotlib inline')
from __future__ import print_function
import sys
import os
import platform
import shutil
import numpy as np
import pandas as pd
# Import flopy
import flopy
from flopy.utils.reference import SpatialReference
from flopy.export.shapefile_utils import recarray2shp, shp2recarray
from flopy.utils.geometry import Polygon, LineString, Point
import matplotlib.pyplot as plt
import cartopy.crs as ccrs



# In[2]:


flopy.utils.reference.epsgRef


# In[3]:


# Set up the paths
basepath = os.path.abspath(os.path.join('data'))
if platform.system() == 'Windows':
    binpath = os.path.join(basepath, 'bin')
else:
    binpath = os.path.join(basepath, 'bin', 'mac')


# ### Setup a New Directory and Change Paths
# For this tutorial, we will work in the model directory.  We can use some fancy Python tools to help us manage the directory creation.  Note that if you encounter path problems with this workbook, you can stop and then restart the kernel and the paths will be reset.

# In[4]:


# Set the name of the path to the model working directory
dirname = 'model'
modelpath = os.path.join(r'/Users/andrewrich_old/Documents/scwa/sv_model','lith_V9')
modelname = 'sv_model_grid_6layers'
print('Name of model path: ', modelpath)

# Now let's check if this directory exists.  If not, then we will create it.
if os.path.exists(modelpath):
    print('Model working directory already exists.')
else:
    print('Creating model working directory.')
    os.mkdir(modelpath)


# ### Define the Model Extent, Grid Resolution, and Characteristics
# It is normally good practice to group things that you might want to change into a single code block.  This makes it easier to make changes and rerun the code.

# In[5]:


fb = flopy.modflow.Modflow.load(os.path.join(
    modelname+'.nam')
                                , version='mf2005', model_ws=modelpath, verbose=True)


lowerleft = [ 6436682.01941381,  1791562.92451396]

fb.sr = SpatialReference(delr=fb.dis.delr, delc=fb.dis.delc, xll=lowerleft[0], yll=lowerleft[1], units='feet',
                        proj4_str='EPSG:2871', rotation=23)


fb.sr


# ## Flopy Tutorial 1: Running the Model
# 
# Flopy has several methods attached to the model object that can be used to run the model.  They are run_model, run_model2, and run_model3.  Here we use run_model3, which will write output to the notebook.

# In[6]:


# Imports for plotting and reading the MODFLOW binary output file

import flopy.utils.binaryfile as bf

# Create the headfile object and grab the results for last time.
headfile = os.path.join(modelpath,'output', modelname + '.hds')

headfileobj = bf.HeadFile(headfile)

# Get a list of times that are contained in the model
times = headfileobj.get_times()
print('Headfile (' + modelname + '.hds' + ') contains the following list of times: ', times[0:10])


# In[7]:


#Get a numpy array of heads for totim = 1.0
#The get_data method will extract head data from the binary file.
head = headfileobj.get_data(totim=times[0])

#Print statistics on the head
print('Head statistics')
print('  min: ', head.min())
print('  max: ', head.max())
print('  std: ', head.std())


# ### Use the Flopy ModelMap Capabilities to Make Plots
# Mapping capabilities are available in flopy as part of [flopy.plot.ModelMap](http://modflowpy.github.io/flopydoc/map.html) to help with plotting.  Here are a couple of examples.

# In[8]:


fb.dis.sr


# In[9]:



from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.io.img_tiles as cimgt

def make_map(projection=ccrs.PlateCarree()):
    fig, ax = plt.subplots(figsize=(9, 13),
                           subplot_kw=dict(projection=projection))
    gl = ax.gridlines(draw_labels=False)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    return fig, ax


# In[19]:


extent = [-122.75,-122.35,38.0,38.4]

# request = cimgt.GoogleTiles()
request = cimgt.StamenTerrain()
# request = cimgt.Image()
# request = cimgt.OSM()
fig, ax = make_map(projection=ccrs.epsg(2871))
ax.set_extent(extent)

ax.add_image(request, 10)
modelmap = flopy.plot.ModelMap(model=fb,ax= ax)
modelmap.plot_array(head,ax=ax,transform=ccrs.epsg(2871))
modelmap.contour_array(head, levels=np.arange(-50, 500, 25),ax=ax)
# modelmap.plot_ibound(ax = ax)
modelmap.plot_inactive()


# In[ ]:




