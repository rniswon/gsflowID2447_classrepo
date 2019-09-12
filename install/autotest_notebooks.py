# Remove the temp directory and then create a fresh one
import os
import shutil
import subprocess

nbdir = os.path.join('..', 'exercises', 'saghen_prms', 'notebook')
#faqdir = os.path.join('..', 'examples', 'FAQ')

# -- make working directories
ddir = os.path.join(nbdir, 'data')
if os.path.isdir(ddir):
    shutil.rmtree(ddir)
os.mkdir(ddir)

tempdir = os.path.join('.', 'temp')
if os.path.isdir(tempdir):
    shutil.rmtree(tempdir)
os.mkdir(tempdir)

testdir = os.path.join('.', 'temp', 'Notebook')
if os.path.isdir(testdir):
    shutil.rmtree(testdir)
os.mkdir(testdir)


def get_Notebooks(dpth):
    return [f for f in os.listdir(dpth) if f.endswith('.ipynb')]


def run_notebook(dpth, fn):
    # run autotest on each notebook
    pth = os.path.join(dpth, fn)
    cmd = 'jupyter ' + 'nbconvert ' + \
          '--ExecutePreprocessor.timeout=600 ' + \
          '--to ' + 'notebook ' + \
          '--execute ' + '{} '.format(pth) + \
          '--output-dir ' + '{} '.format(testdir) + \
          '--output ' + '{}'.format(fn)
    ival = os.system(cmd)
    try:
        assert ival == 0, 'could not run {}'.format(fn)
        print("{}...............ok.".format(fn))
    except:
        print("{}...............Failed.".format(fn))


def test_notebooks():

#    for dpth in [faqdir, nbdir]:
    for dpth in [nbdir]:

        # get list of notebooks to run
        files = get_Notebooks(dpth)

        # run each notebook
        for fn in files:
            yield run_notebook, dpth, fn


if __name__ == '__main__':
    jnbs = ['0_model_boundary.ipynb', '1_fishnet_params.ipynb', '2_dem_parameters.ipynb',
            '3_dem_2_streams_parameters.ipynb',
     '4_crt_fill_parameters.ipynb', '5_stream_parameters.ipynb', '6_veg_parameters.ipynb',
     '7_soil_parameters.ipynb', '8_climate_parameters.ipynb', '9_impervious_parameters.ipynb',
            'climate_zones.ipynb', 'Config_modify.ipynb']
    if 1:
        print("Testing PRMS arcpy notebooks......")
        for fn in jnbs:
            dpth = r"..\\exercises\\saghen_prms\\notebook"
            run_notebook(dpth, fn)
    if 1:
        print("Testing Modflow notebook......")
        jnbs = ['Groundwater_modeling_intro.ipynb']
        for fn in jnbs:
            dpth = r"..\\exercises\\saghen_modflow"
            run_notebook(dpth, fn)

    print("Testing pyGsflow notebook......")
    jnbs = ['1_pygsflow_intro.ipynb', '2_Assemble_GSFLOW_model.ipynb', '3_Model_Sensitivity_Calibration.ipynb']
    for fn in jnbs:
        dpth = r"..\\exercises\\\saghen_pyGSFLOW"
        run_notebook(dpth, fn)



