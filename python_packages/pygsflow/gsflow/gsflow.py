# -*- coding: utf-8 -*-
import os, sys
import logging
from control import Control
from prms import Prms
import supports
import flopy


def load(control_file):
    gs = Gsflow(control_file=control_file)
    gs.load()
    return gs

class Gsflow():
    def __init__(self, control_file=None, prms=None, mf=None, mf_load_only=None,
                 prms_load_only=None, gsflow_exe=None):

        self.control_file = control_file
        self.ws = None
        self.mf_load_only = mf_load_only
        self.prms_load_only = prms_load_only

        if gsflow_exe == None:
            self.gsflow_exe = os.path.join(os.path.dirname(__file__), r"bin\gsflow.exe")

        # initialize prms
        if prms and isinstance(prms, Prms):
            self.prms = prms
        else:
            self.prms = None
            # todo: generate an msg

        # inialize flopy
        if mf and isinstance(mf, flopy.modflow.Modflow):
            self.mf = mf
        else:
            self.mf = None
            # todo: generate an error
        self.load()

    def load(self):
        # load control file
        if not (os.path.isfile(self.control_file)):
            raise ValueError("Cannot find control file")

        self.control = Control(control_file=self.control_file)
        print("Control file is loaded")

        # load prms
        self.prms = Prms(control=self.control)
        print("PRMS files are loaded")

        # load modflow
        mode = self.control.get_values('model_mode')
        if 'GSFLOW' in mode[0] or 'MODFLOW' in mode[0]:
            fname = self.control.get_values('modflow_name')
            fname = supports._get_file_abs(control_file=self.control_file, fn=fname[0])
            self._load_modflow(fname)
            self.mf.namefile = os.path.basename(self.control.get_values('modflow_name')[0])

    def _load_modflow(self, fname):
        """
        The package files in the .nam file are relative to the execuatble gsflow. So here, we generate a temp.nam
        file that that has the absollute files
        :return:
        """

        fidr = open(fname, 'r')
        content = fidr.readlines()
        fidr.close()
        temp_fn = os.path.basename(fname).split('.')[0] + "_gsflow_temp_.nam"

        mf_dir = os.path.dirname(fname)
        temp_fn = os.path.join(mf_dir, temp_fn)
        fidw = open(temp_fn, 'w')
        for line in content:
            line = line.strip()
            if line[0] == '#':
                continue
            parts = line.split()
            pkg_nm = parts[0]
            pkg_un = parts[1]
            pkg_fn = parts[2]
            pkg_fn = os.path.basename(pkg_fn)
            # pkg_fn = os.path.join(mf_dir,pkg_fn)
            txt = "{} {} {}\n".format(pkg_nm, pkg_un, pkg_fn)
            fidw.write(txt)
        fidw.close()
        bas_nam = os.path.basename(temp_fn)
        self.mf = flopy.modflow.Modflow.load(temp_fn, model_ws=mf_dir)

    # def change_ws(self, ws):
    #
    #     if os.path.isdir(ws):
    #         print("Warning: The {} directory already exists".format(ws))
    #     parent_folder = os.path.dirname(ws)
    #
    #     if not (os.path.isdir(parent_folder)):
    #         raise ValueError(" The parent directory {} doesn't exist...".format(parent_folder))
    #
    #     if not (os.path.isdir(ws)):
    #         os.mkdir(ws)
    #
    #     self.ws = ws
    #
    #     # change control file location
    #     fnn = os.path.basename(self.control.control_file)
    #     self.control.control_file = os.path.join(self.ws, fnn)
    #
    #     # change parameters
    #     for par_record in self.prms.Parameters.parameters_list:
    #         curr_file = os.path.basename(par_record.file_name)
    #         curr_file = os.path.join(self.ws, curr_file)
    #         par_record.file_name = curr_file
    #
    #     # change datafile
    #     curr_file = os.path.basename(self.prms.Data.data_file)
    #     curr_file = os.path.join(self.ws, curr_file)
    #     self.prms.Data.data_file = curr_file
    #
    #     # change mf
    #     if not (self.mf == None):
    #         self.mf.change_model_ws(self.ws)

    # def change_base_file_name(self, filename):
    #     # change control file location
    #     cnt_file = filename + "_cnt" + ".control"
    #     dir__ = os.path.dirname(self.control.control_file)
    #     self.control.control_file = os.path.join(dir__, cnt_file)
    #
    #     # change parameters
    #     for index, par_record in enumerate(self.prms.Parameters.parameters_list):
    #         curr_file = os.path.basename(par_record.file_name)
    #         curr_file = os.path.join(self.ws, curr_file)
    #         par_record.file_name = curr_file
    #
    #     # change datafile
    #     curr_file = os.path.basename(self.prms.Data.data_file)
    #     curr_file = os.path.join(self.ws, curr_file)
    #     self.prms.Data.data_file = curr_file
    #     pass

    def _get_relative_path(self, fn):
        """
        If relative files are used, they should be relative to the control file

        :return: relative path with respect to control file
        """
        control_file_abs = os.path.absfile(self.control)
        fn_abs = os.path.absfile(fn)
        # find common path
        rel_dir = os.path.relpath(os.path.dirname(fn), os.path.dirname(control_file_abs))
        rel_path = os.path.join(rel_dir + os.path.basename(fn))
        return rel_path

    # def _mk_dir(self, dir_):
    #     if not (os.path.isdir(dir_)):
    #         os.mkdir(dir_)
    #     else:
    #         print(" Warning:  the directory exists {}".format(dir_))

    def write_input(self, basename=None, workspace=None):
        """
        :param basename:
        :param workspace:
        :return:
        Write input files for gsflow. Four cases are possible:
        (1) if basename and workspace are None,then the exisiting files will be overwritten
        (2) if basename is specified, only file names will be changes
        (3) if only workspace is specified, only folder will be changed
        (4) when both basename and workspace are specifed both files are changed

        """
        # overwrite
        if basename == None and workspace == None:
            print("Warning: input files will be overwritten....")
            self._write_all()
            return

        # only change the directory
        if (basename == None) and (not (workspace == None)):
            if not (os.path.isdir(workspace)):
                os.mkdir(workspace)
            fnn = os.path.basename(self.control.control_file)
            self.control.control_file = os.path.join(workspace, fnn)
            self.control_file = os.path.join(workspace, fnn)
            self.prms.control_file = self.control_file
            # change parameters
            parm_file_list = []
            for par_record in self.prms.parameters.parameters_list:
                curr_file = os.path.basename(par_record.file_name)
                curr_file = os.path.join(workspace, curr_file)
                par_record.file_name = curr_file
                parm_file_list.append(curr_file)

            # change datafile
            curr_file = os.path.basename(self.prms.Data.data_file)
            curr_file = os.path.join(workspace, curr_file)
            self.prms.Data.data_file = curr_file

            # change mf
            if not (self.mf == None):
                self.mf.change_model_ws(workspace)

            # update file names in control object
            for rec_name in self.control._gslow_files:
                if rec_name in self.control._record_names:
                    file_values = self.control.get_values(rec_name)
                    file_value = []
                    for fil in file_values:
                        cnt_dir = os.path.dirname(self.control_file)
                        va = os.path.join(cnt_dir, os.path.basename(fil))
                        file_value.append(va)
                    self.control.set_values(rec_name, file_value)

            # write
            self.prms.control = self.control
            self._write_all()
            return

        # only change the basename
        if (not (basename == None)) and (workspace == None):
            cnt_file = basename + "_cont.control"
            ws_ = os.path.dirname(self.control.control_file)
            self.control.control_file = os.path.join(ws_, cnt_file)
            self.control_file = os.path.join(ws_, cnt_file)
            self.prms.control_file = self.control_file
            # change parameters
            for ifile, par_record in enumerate(self.prms.Parameters.parameters_list):
                par_file = basename + "_par_{}.params".format(ifile)
                curr_dir = os.path.dirname(par_record.file_name)
                curr_file = os.path.join(curr_dir, par_file)
                par_record.file_name = curr_file

            # change datafile
            dfile = basename + "_dat.data"
            curr_dir = os.path.dirname(self.prms.Data.data_file)
            curr_file = os.path.join(curr_dir, dfile)
            self.prms.Data.data_file = curr_file

            # change mf
            if not (self.mf == None):
                self.mf.change_base_file_name(basename)

            # update file names in control object
            for rec_name in self.control._gslow_files:
                if rec_name in self.control._record_names:
                    file_values = self.control.get_values(rec_name)
                    file_value = []
                    for fil in file_values:
                        dir_name = os.path.dirname(fil)
                        if rec_name == 'modflow_name':
                            mfname = basename+".nam"
                            filvalue = os.path.join(dir_name, mfname)
                        else:
                            vvfile = rec_name.split("_")
                            del vvfile[-1]
                            vvfile = vvfile.join("_")
                            ext = fil.split(".")[-1]
                            vvfile = basename + "_" + vvfile + "." + ext
                            filvalue = os.path.join(dir_name, vvfile)

                        file_value.append(os.path.basename(filvalue))
                    self.control.set_values(rec_name, file_value)
            self.prms.control = self.control
            self._write_all()
            return

        # change both directory & basename
        if (not (basename == None)) and (not (workspace == None)):
            if not (os.path.isdir(workspace)):
                os.mkdir(workspace)
            cnt_file = basename + "_cont.control"
            self.control.control_file = os.path.join(workspace, cnt_file)
            self.prms.control_file = self.control.control_file
            self.control_file = self.control.control_file

            # change parameters
            for ifile, par_record in enumerate(self.prms.Parameters.parameters_list):
                par_file = basename + "_par_{}.params".format(ifile)
                curr_file = os.path.join(workspace, par_file)
                par_record.file_name = curr_file

            # change datafile
            dfile = basename + "_dat.data"
            curr_file = os.path.join(workspace, dfile)
            self.prms.Data.data_file = curr_file

            # change mf
            if not (self.mf == None):
                self.mf.change_model_ws(workspace)
                self.mf.change_base_file_name(basename)

            ## TODO: Update control file
            # update file names in control object
            for rec_name in self.control._gslow_files:
                if rec_name in self.control._record_names:
                    file_values = self.control.get_values(rec_name)
                    file_value = []
                    for fil in file_values:
                        dir_name = os.path.dirname(fil)
                        if rec_name == 'modflow_name':
                            mfname = basename + ".nam"
                            filvalue = os.path.join(dir_name, mfname)
                        else:
                            vvfile = rec_name.split("_")
                            del vvfile[-1]
                            vvfile = vvfile.join("_")
                            ext = fil.split(".")[-1]
                            vvfile = basename + "_" + vvfile + "." + ext
                            filvalue = os.path.join(dir_name, vvfile)

                        file_value.append(os.path.basename(filvalue))
                    self.control.set_values(rec_name, file_value)

                    # update file names in control object
                    for rec_name in self.control._gslow_files:
                        if rec_name in self.control._record_names:
                            file_values = self.control.get_values(rec_name)
                            file_value = []
                            for fil in file_values:
                                dir_name = os.path.dirname(fil)
                                if rec_name == 'modflow_name':
                                    mfname = basename + ".nam"
                                    filvalue = os.path.join(workspace, mfname)
                                else:
                                    vvfile = rec_name.split("_")
                                    del vvfile[-1]
                                    vvfile = vvfile.join("_")
                                    ext = fil.split(".")[-1]
                                    vvfile = basename + "_" + vvfile + "." + ext
                                    filvalue = os.path.join(workspace, vvfile)

                                file_value.append(os.path.basename(filvalue))
                            self.control.set_values(rec_name, file_value)
            self.prms.control = self.control
            self._write_all()
            return

    def _write_all(self):

        # write control
        print("Control file is written...")
        self.control.write()

        # self write parameters
        print("Parameters files are written...")
        self.prms.parameters.write()

        # write data
        print("Data file is written...")
        self.prms.Data.write()

        # write mf
        print("Modflow files are written...")
        if not (self.mf == None):
            self.mf.write_input()

    def run(self):
        fn = self.control_file
        cnt_folder = os.path.dirname(fn)
        script_dir = os.getcwd()

        # write bat file
        bat_file = os.path.join(cnt_folder, "__gsflow_runner.bat")
        fid = open(bat_file, 'w')
        cmd = self.gsflow_exe + " " + os.path.basename(self.control_file)
        fid.write(cmd)
        fid.close()

        os.chdir(cnt_folder)
        os.system("__gsflow_runner.bat")
        os.chdir(script_dir)

        print("Gsflow runing finished.....")
