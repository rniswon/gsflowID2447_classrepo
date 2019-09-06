import sys, os
from shutil import copyfile

Env_name = sys.argv[1]
pths_to_add = []

#
fidr = open("environment.yml", 'r')
contents = fidr.readlines()
fidr.close()

# write env file
fidw = open("environment_class.yml", 'w')
for line in contents:
    if 'name' in line:
        fidw.write('name: {}'.format(Env_name))
        fidw.write('\n')
    else:
        fidw.write(line)

fidw.close()


if 1:
    print("------------- Create a new environment from yalm file ---------------")
    os.system("conda env create -f environment_class.yml")

# get conda info
conda_info = os.popen('conda info --envs').read()
conda_info = conda_info.split('\n')
env_found = False
env_path = None
for env in conda_info:
    if Env_name in env:
        env_found = True
        env_path = env.split()[-1]
        if not (os.path.isdir(env_path)):
            print("Cannot locate the environment folder. Download Flopy and PyGSFLOW mannually")

        break



if not (env_found) | (env_path is None):
    print("Cannot locate the environment folder. Download Flopy and PyGSFLOW mannually")

if not (env_path is None):
    print("Download other packages ...")


    # flopy
    base_folder = os.getcwd()

    print("--------- Install flopy.....")
    os.chdir(r"..\python_packages")
    pkg_folder = os.getcwd()
    flopy_loc =  pkg_folder + r"\flopy"
    pths_to_add.append(flopy_loc)
    lists =  os.listdir(pkg_folder)
    if 'flopy' in lists:
        pass
    else:
        os.system('git clone https://github.com/modflowpy/flopy.git')

    # pygsflow
    lists = os.listdir(pkg_folder)
    if 'pygsflow' in lists:
        pass
    else:
        os.system('git clone https://github.com/pygsflow/pygsflow.git')
    gsflow_loc = pkg_folder + r"\pygsflow"
    pths_to_add.append(gsflow_loc)
    site_pkg = env_path + r"\Lib\site-packages\gsflow_class.pth"
    fidw = open(site_pkg, 'w')
    for line in pths_to_add:
        fidw.write(line)
        fidw.write("\n")
    fidw.close()
    os.chdir(base_folder)

    site_pkg = env_path + r"\Lib\site-packages\arcpy.pth"
    copyfile('arcpy.pth', site_pkg)








