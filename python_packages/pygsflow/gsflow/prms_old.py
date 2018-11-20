# -*- coding: utf-8 -*-

import os,sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from prms_par import prms_par
import subprocess
from subprocess import PIPE, STDOUT


class Prms_base(prms_par):
    def __init__(self, gsflow_control = None):

        self.exe_prms = None # Todo : remove
        self.gsflow_control = gsflow_control
        self.control_file = None
        self.prms_data = None
        self.prms_parameters = None

    def join_rel_abs_path(self,relpath,abspath):
        dfile = relpath
        wc = abspath
        if os.path.isabs(dfile):
            fnn = dfile
        elif relpath[0] != '.':
            fnn = os.path.join(abspath,relpath)
        else:
            if sys.platform == "linux" or sys.platform == "linux2":
                fileparts = dfile.split("/")
                wcparts = wc.split("/")

            elif sys.platform == "win32":
                fileparts = dfile.split("/")
                wcparts = wc.split("\\")

            del(fileparts[0])
            del(wcparts[-1])
            part1 = '\\'.join(wcparts)
            part2 = '\\'.join(fileparts)
            fnn = os.path.join(part1, part2)
        if sys.platform == "linux" or sys.platform == "linux2":
            fnn = "/" + fnn
        return fnn

    def _get_file_abs(self, fn):
        control_folder = os.path.dirname(self.control_file)
        abs_file = os.path.abspath(os.path.join(control_folder, fn[0]))
        return  abs_file

    def read_data_file(self):
        data_file = self.gsflow_control['data_file'][2]
        data_file = self._get_file_abs(data_file)
        data_items = ['tmax', 'tmin', 'precip',  'runoff', 'pan_evap', 'solrad', 'from_data', 'rain_day']
        data_dict = dict()
        fid = open(data_file, 'r')
        data_dict['Comments'] = fid.readline().strip()
        columns = []
        while True:
            line = fid.readline()
            if line.strip() == '' or line.strip()[0:2] == '//':
                continue
            if "####" in line:
                break

            if any(item in line for item in data_items):
                val_nm = line.strip().split()
                for val in range(int(val_nm[1])):
                    columns.append(val_nm[0]+"_" + str(val))
        columns = ['Year', 'Month', 'Day', 'Hour', 'Minut', 'Second'] + columns
        data_dict['data'] = pd.read_csv(fid, delim_whitespace=True, names=columns)
        fid.close()
        self.prms_data = data_dict

    def read_para_file(self):

        # loop over muptiple files if there is any
        parafiles = self.gsflow_control['param_file'][2]
        wc = self.work_directory
        par_order = []
        dim_order = []
        par_widths = dict()
        Dimensions = dict()
        Parameters = dict()
        dimen_part = []
        para_part = []
        for file in parafiles:
            fnn = self.join_rel_abs_path(file, wc)
            with open(fnn, 'r') as data_file:
                content = data_file.read()
            # the content consists of two parts: Dimensions & Parameters
            # Split the file content into two parts based on the delimiter "**"
            content = content.split("**")
            read_param_flg = False
            read_dim_flg = False
            for ig, fgroup in enumerate(content):
                # always skip first record
                if "Parameters" in fgroup:
                    read_param_flg = True
                    continue

                if "Dimensions" in fgroup:
                    read_dim_flg = True
                    continue

                if read_param_flg:
                    if len(para_part)>0:
                        if para_part[-1] == '\n' and fgroup[0]=='\n':
                            fgroup = fgroup[1:]
                        elif para_part[-1] != '\n' and fgroup[0]!='\n':
                            para_part = para_part + "\n"
                            
                        para_part = para_part + fgroup
                    else:
                        para_part = fgroup
                    read_param_flg = False
                    continue

                if read_dim_flg:
                    if len(dimen_part)>0:
                        if len(dimen_part) > 0:
                            if dimen_part[-1] == '\n' and fgroup[0] == '\n':
                                fgroup = fgroup[1:]
                            if dimen_part[-1] != '\n' and fgroup[0] != '\n':
                                dimen_part = dimen_part + "\n"
                        dimen_part = dimen_part + fgroup
                    else:
                        dimen_part = fgroup
                    read_dim_flg = False
                    continue



            # if len(content) == 1:
            #     dimen_part = []
            #     para_part = content[0]
            # else:              
            #     dimen_part = content[2]
            #     para_part = content[4]
            



        # Split each based on "\n####"
        try:
            dimen_part= dimen_part.split("\n####\n")
        except:
            pass
        for record in dimen_part:
            # each record consists of a record name and a value
            if len(record)>0:
                rec = record.split("\n")
                Dimensions[rec[0]]=rec[1]
                dim_order.append(rec[0])
        if len(dimen_part) == 0:
            para_part = para_part.split("####\n")
        else:
            para_part = para_part.split("\n####\n")

        idx = 0
        for record in para_part:

            if record == '':
                pass
            else:

                idx = idx + 1
                print idx
                # each record consists of 7 parts
                if len(record)>0:
                    rec = record.split("\n")
                    # 1) is the name
                    par_name = rec[0].split()[0]
                    par_order.append(par_name)
                    # 2) this is width, something not used in prms
                    try:
                        width = rec[0].split()[1] # not sure Ask Rich
                        par_widths[par_name]=width
                    except:
                        par_widths[par_name] = ''
                    # 3) No_dimension : 1d versus 2d
                    try:
                        no_dim = int(rec[1])
                    except:
                        pass

                    # dimension names
                    dim_names = []
                    indx = 2
                    for dim in np.arange(no_dim):
                        dim_names.append(rec[indx])
                        indx = indx + 1

                    nvalues = rec[indx]
                    indx = indx + 1
                    value_type = int(rec[indx])
                    indx = indx + 1
                    values = rec[indx:]
                    if values[-1]=='':
                        del(values[-1])
                    if value_type == 1: # int
                        values = [int(value) for value in values]
                    elif value_type == 2 or value_type == 3: # real
                        if values[-1]=='####':
                            del values[-1]

                        values = [float(value) for value in values]
                    values = np.array(values)
                    Parameters[par_name] = [no_dim, dim_names,nvalues, value_type, values]

            prms_param_file = dict()
            prms_param_file['Dimensions'] = Dimensions
            prms_param_file['Parameters'] = Parameters
            prms_param_file['widths'] = par_widths
            self.prms_parameters = prms_param_file
            self.fields_order['par_order'] = par_order
            self.fields_order['dim_order'] = dim_order


    def _load(self):

        self.read_data_file()
        print ("Reading the parameters file ....")
        self.read_para_file()
        pass

    def run(self):
        fn = self.control_file_name
        fparts = fn.split('\\')
        del (fparts[-1])
        fn2 = '\\'.join(fparts)
        script_dir = os.getcwd()
        os.chdir(fn2)
        os.system("gsflow.bat")
        os.chdir(script_dir)


    def get_parameter(self, name):
        """
        :param name:
        :return:
        """

        dims = self.prms_parameters['Dimensions'].keys()
        params = self.prms_parameters['Parameters'].keys()

        if name in dims:
            curr_par = self.prms_parameters['Dimensions'][name]
            par_object = prms_par()
            par_object.name = name
            par_object.values = int(curr_par[1])

        elif name in params:
            curr_par = self.prms_parameters['Parameters'][name]
            par_object = prms_par()
            par_object.name = name
            par_object.read_param(curr_par)
            return par_object

        else:
            str_err = name + " is not a defined parameter"
            print str_err

    def set_parameter(self, par):
        # par is a list that has the all param info
        
        pass

    def write_seperate_param_file(self, fn):
        pass

    def write_param_file(self, fn):

        par_dict = self.prms_parameters
        dims = par_dict['Dimensions']
        parms = par_dict['Parameters']
        dim_order = self.fields_order['dim_order']
        par_order = self.fields_order['par_order']

        fid = open(fn,'w')

        # write header
        header1 = "Generated by pyprms, Author: Ayman Alzraiee\n"
        header2 = "Version: 1.7\n"
        fid.write(header1)
        fid.write(header2)

        # write the dimension part
        fid.write('** Dimensions **\n')

        for dim in dim_order:
            print dim
            fid.write('####\n')
            fid.write(dim)
            fid.write('\n')
            fid.write(str(dims[dim]))
            fid.write('\n')

        # write the parameters
        fid.write('** Parameters **\n')

        for par in par_order:
            fid.write('####\n')
            curr_par = parms[par]
            # parameter name
            fid.write(par)
            fid.write('\n')

            # number of dimensions
            fid.write(str(curr_par[0]))
            fid.write('\n')


            # dimensions names
            for pp in curr_par[1]:
                fid.write(pp)
                fid.write('\n')

            # number of values
            fid.write(str(curr_par[2]))
            fid.write('\n')

            # type of values

            fid.write(str(curr_par[3]))
            fid.write('\n')

            # values
            for val in curr_par[4]:
                if curr_par[3] == 1: # int
                    fid.write(str(int(val)))
                    fid.write('\n')
                else:
                    fid.write(str(val))
                    fid.write('\n')


            #fid.write('####\n')

        fid.close()

    def write_control_file(self,fn):

        cont_dict = self.gsflow_control
        field_order = self.fields_order['control_order']
        fid = open(fn, 'w')

        # write header
        header1 = "GSFLOW control File. Generated by pyprms, Author: Ayman Alzraiee\n"
        fid.write(header1)

        for par in field_order:
            fid.write('####\n')
            curr_par = cont_dict[par]
            # parameter name
            fid.write(par)
            fid.write('\n')

            # number of values
            fid.write(str(curr_par[0][0]))
            fid.write('\n')

            # data type
            fid.write(str(curr_par[1]))
            fid.write('\n')

            # values
            for val in curr_par[2]:
                fid.write(str(val))
                fid.write('\n')
        fid.close()

    def write_data_file(self,fn):
        data_dict = self.prms_data
        climate_keys = ['precip','tmax', 'tmin', 'solrad', 'pan_evap', 'runoff','from_data']
        existing_keys = data_dict.keys()
        fid = open(fn, 'w')

        # write header
        header1 = "Generated by pyprms, Author: Ayman Alzraiee\n"
        fid.write(header1)

        # write data types and number of stations
        header2 = ''
        Mdata = np.array([])


        for ckey in climate_keys:
            if ckey in existing_keys:
                ts_data = data_dict[ckey]
                if not (type(ts_data) == np.ndarray):
                    ts_data = np.array(ts_data)
                nsta = ts_data.shape[1]
                lin = ckey+ ' ' + str(nsta) + '\n'
                fid.write(lin)
                header2 = header2 + '          '+ ckey
                if Mdata.shape[0]==0:
                    Mdata = ts_data
                else:
                    Mdata = np.hstack((Mdata,ts_data))


        # write data header
        header2 = '###################           '+header2 + '\n'
        fid.write(header2)

        # write data
        cdate = data_dict['Date']
        indx = 0
        for row in Mdata:
            curr_date = cdate[indx]
            if type(curr_date) == datetime.date:
                curr_date = curr_date.strftime("%Y %m %d 0 0 0 ")
                str1 = curr_date
            else:
                str1 = ''.join(str(e) + ' ' for e in curr_date)
            str2 = ''.join("%10.4f"%e + ' ' for e in row)
            fid.write(str1 + str2)
            fid.write('\n')
            indx = indx + 1

        fid.close()
        pass

    def add_parameter(self):
        pass

    def remove_parameter(self, pr):
        self.prms_parameters
        try:
            del (self.prms_parameters['Parameters'][pr])
            self.fields_order['par_order'].remove(pr)

        except ValueError:
            print "Cannot remove " + pr + "parameter......"








