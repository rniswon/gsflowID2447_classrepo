from gsflow import Gsflow
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from flopy.utils.reference import SpatialReference
import scipy.ndimage
from skimage import transform
from scipy import misc

hru_shp_file = r"D:\Workspace\training\gsflowID2447_classrepo\exercises\saghen_mf\data\hru_params.shp"
hru_shp = gpd.read_file(hru_shp_file)
hru_shp = hru_shp.sort_values(by=['HRU_ID'])
nrows, ncols = hru_shp.HRU_ROW.max(), hru_shp.HRU_COL.max()
ibound = hru_shp['HRU_TYPE'].values.reshape(nrows, ncols)
control_file = r"D:\Workspace\Codes\gsflow\gsflow\data\data_backup\data\sagehen\windows\gsflow.control"
gs = Gsflow(control_file = control_file )

def im_transform(a, angle, shift, scale):
    
    angle = np.pi * angle/180.0
    tf = transform.SimilarityTransform(scale=scale, rotation=angle, translation=shift)
    maxV = a.max()
    minV = a.min()
    imag_ = np.interp(a, (a.min(), a.max()), (-1, +1))
    new_iamge = transform.warp(imag_,  tf)
    new_iamge = np.interp(new_iamge, (new_iamge.min(), new_iamge.max()), (minV, maxV))
    return new_iamge




rot_angle = (4367636 - 4367936.7)/(216026-214646.164)
angle = np.abs(np.degrees(rot_angle))
aa = gs.mf.bas6.ibound.array[0,:,:]
aa2 = misc.imresize(aa, (77,84), mode='F')

def cal_diff(aa2, ibound, angle=angle, shift=[0,0], scale=[1,1] ):
    xx = im_transform(aa2, angle=angle, shift=shift, scale=scale)
    return xx-ibound

def extract_infoo(aa, angle=angle, shift=[0,0], scale=[1,1]):
    aa2 = misc.imresize(aa, (77, 84), mode='F')
    xx = im_transform(aa2, angle=angle, shift=shift, scale=scale)    
    return xx
    
# xi = np.linspace(1, gs.mf.ncol, gs.mf.ncol)
# yi = np.linspace(1, gs.mf.nrow, gs.mf.nrow)
# mf_cols, mf_rows = np.meshgrid(xi, yi)
# mf_cols= scipy.ndimage.interpolation.rotate(mf_cols, angle)
# nrrow, nccol = mf_cols.shape
# xi = np.linspace(1, nccol, nccol)
# yi = np.linspace(1, nrrow, nrrow)
# mf_cols, mf_rows = np.meshgrid(xi, yi)
# #mf_cols= scipy.ndimage.interpolation.rotate(mf_cols, angle)
# #mf_rows= scipy.ndimage.interpolation.rotate(mf_rows, angle)
# mf_cols = mf_cols.flatten()
# mf_rows = mf_rows.flatten()
# pass
#
# if False:
#     xi = np.linspace(1,gs.mf.ncol, gs.mf.ncol)
#     yi = np.linspace(1, gs.mf.nrow, gs.mf.nrow)
#     mf_cols, mf_rows = np.meshgrid(xi, yi)
#     mf_cols = mf_cols.flatten()
#     mf_rows = mf_rows.flatten()
# 
# del_col = 8
# del_row = 0
# grows =  mf_rows - del_row - 1
# gcols = mf_cols - del_col - 1
# grows = grows.astype('int')
# gcols = gcols.astype('int')


#### UPW data
## hk1
#val = scipy.ndimage.interpolation.rotate(gs.mf.lpf.hk.array[0,:,:], angle)
#Zmat = np.zeros((nrows, ncols))
#Zmat[grows, gcols] = val.flatten()
#Zmat[Zmat<=0] = np.mean(Zmat[Zmat>0] )
val = gs.mf.lpf.hk.array[0,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('hk1.txt', Zmat)

#hk2
val = gs.mf.lpf.hk.array[1,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('hk2.txt', Zmat)

#sy1
val = gs.mf.lpf.sy.array[0,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[np.isnan(Zmat)] = vv
Zmat[Zmat<=0] = vv
np.savetxt('sy1.txt', Zmat)

#sy1
val = gs.mf.lpf.sy.array[1,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('sy2.txt', Zmat)

#ss1
val = gs.mf.lpf.ss.array[0,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('ss1.txt', Zmat)
#ss1
val = gs.mf.lpf.ss.array[1,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('ss2.txt', Zmat)


## Starting head data
val = gs.mf.bas6.strt.array[0,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('initial_head1.txt', Zmat)

val = gs.mf.bas6.strt.array[1,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('initial_head2.txt', Zmat)


## uzf
val = gs.mf.uzf.vks.array
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('uzf_vks.txt', Zmat)

## uzf
val = gs.mf.uzf.thts.array
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('uzf_ths.txt', Zmat)

## uzf
val = gs.mf.uzf.finf[0].array
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = vv
Zmat[np.isnan(Zmat)] = vv
np.savetxt('uzf_finf.txt', Zmat)

## dis
val = gs.mf.dis.thickness.array[0,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = 1.0
Zmat[np.isnan(Zmat)] = 1.0
np.savetxt('thickness1.txt', Zmat)

val = gs.mf.dis.thickness.array[1,:,:]
Zmat = extract_infoo(val, angle=angle, shift=[13,-13], scale=[1,1] )
Zmat[ibound==0] = np.nan
vv = np.nanmean(Zmat[Zmat>0])
Zmat[Zmat<=0] = 1.0
Zmat[np.isnan(Zmat)] = 1.0
np.savetxt('thickness2.txt', Zmat)

pass




pass

