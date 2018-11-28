# -*- coding: utf-8 -*-
import os, sys
import logging
from control import Control
from prms import Prms
import supports
import flopy
import subprocess as sp

if sys.version_info > (3, 0):
    import queue as Queue
else:
    import Queue
from datetime import datetime
import threading


def load(control_file):
    gs = Gsflow(control_file=control_file)
    gs.load()
    return gs


class Gsflow():
    def __init__(self, control_file=None, prms=None, mf=None, mf_load_only=None,
                 prms_load_only=None, gsflow_exe=None):

        print ("PyGSFLOW ------ V0.0")

        self.control_file = os.path.abspath(control_file)
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
        print("Working on loading PRMS model ...")
        self.prms = Prms(control=self.control)

        # load modflow
        mode = self.control.get_values('model_mode')
        if 'GSFLOW' in mode[0] or 'MODFLOW' in mode[0]:
            print ("Working on loading MODFLOW files ....")
            fname = self.control.get_values('modflow_name')
            fname = supports._get_file_abs(control_file=self.control_file, fn=fname[0])
            self._load_modflow(fname)
            self.mf.namefile = os.path.basename(self.control.get_values('modflow_name')[0])
        else:
            print ("There are no Modflow files, PRMS model only")

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
        print ("MOSFLOW files are loaded ... ")

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

        print("Writing the project files .....")
        if not (workspace == None):
            workspace = os.path.abspath(workspace)

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
            new_param_file_list = []
            for par_record in self.prms.parameters.parameters_list:
                curr_file = os.path.basename(par_record.file_name)
                curr_file = os.path.join(workspace, curr_file)
                par_record.file_name = curr_file
                if not (curr_file in new_param_file_list):
                    new_param_file_list.append(curr_file)
            self.control.set_values('param_file', new_param_file_list)

            # change datafile
            curr_file = os.path.basename(self.prms.Data.data_file[0])
            curr_file = os.path.join(workspace, curr_file)
            self.prms.Data.data_file = curr_file
            self.control.set_values('data_file', [curr_file])

            # change mf
            if not (self.mf == None):
                self.mf.change_model_ws(workspace)
                nmfile = os.path.basename(self.mf.name)
                self.mf.name = os.path.join(self.mf.model_ws, nmfile)
                out_files_list = []
                for out_file in self.mf.output_fnames:
                    ext = out_file.split(".")[-1]
                    if out_file.count('.') > 1:
                        ext = out_file.split(".")
                        del ext[0]
                        ext = ".".join(ext)
                    #new_outfn = os.path.join(workspace, basename + "." + ext)
                    new_outfn =  nmfile + "." + ext
                    out_files_list.append(new_outfn)
                self.mf.output_fnames = out_files_list
                mfnm = self.mf.name + ".nam"
                self.control.set_values('modflow_name', [mfnm])

            # update file names in control object
            for rec_name in self.control._gslow_files:
                if rec_name in self.control._record_names:
                    file_values = self.control.get_values(rec_name)
                    file_value = []
                    for fil in file_values:
                        cnt_dir = os.path.dirname(self.control_file)
                        va = os.path.join(workspace, os.path.basename(fil))
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
            flist = self.prms.parameters.parameter_files
            new_param_file_list = []
            for ifile, par_record in enumerate(self.prms.parameters.parameters_list):
                file_index = flist.index(par_record.file_name)
                par_file = basename + "_par_{}.params".format(file_index)
                curr_dir = os.path.dirname(par_record.file_name)
                curr_file = os.path.join(curr_dir, par_file)
                par_record.file_name = curr_file
                if not (curr_file in new_param_file_list):
                    new_param_file_list.append(curr_file)
            self.control.set_values('param_file', new_param_file_list)

            # change datafile
            dfile = basename + "_dat.data"
            curr_dir = os.path.dirname(self.prms.Data.data_file)
            curr_file = os.path.join(curr_dir, dfile)
            self.prms.Data.data_file = curr_file
            self.control.set_values('data_file', [curr_file])

            # change mf
            if not (self.mf == None):
                curr_dir = self.mf.model_ws
                #self.mf.name = os.path.join(curr_dir, basename)
                self.mf.name = os.path.join(curr_dir, basename)
                out_files_list = []
                for out_file in self.mf.output_fnames:
                    ext = out_file.split(".")[-1]
                    if out_file.count('.') > 1:
                        ext = out_file.split(".")
                        del ext[0]
                        ext = ".".join(ext)
                    #new_outfn = os.path.join(workspace, basename + "." + ext)
                    new_outfn =  basename + "." + ext
                    out_files_list.append(new_outfn)
                self.mf.output_fnames = out_files_list
                mfnm = self.mf.name + ".nam"
                self.control.set_values('modflow_name',[mfnm])

            # update file names in control object
            for rec_name in self.control._gslow_files:
                if rec_name in self.control._record_names:
                    if rec_name in ['modflow_name', 'param_file', 'data_file']:
                        continue
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
                            vvfile = "_".join(vvfile)
                            if "." in fil:
                                ext = fil.split(".")[-1]
                            else:
                                ext = "dat"
                            #ext = fil.split(".")[-1]
                            vvfile = basename + "_" + vvfile + "." + ext
                            filvalue = os.path.join(dir_name, vvfile)

                        file_value.append(filvalue)
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
            ## get param files list
            flist = self.prms.parameters.parameter_files
            new_param_file_list = []
            for ifile, par_record in enumerate(self.prms.parameters.parameters_list):
                file_index = flist.index(par_record.file_name)
                par_file = basename + "_par_{}.params".format(file_index)
                curr_file = os.path.join(workspace, par_file)
                par_record.file_name = curr_file
                if not (curr_file in new_param_file_list):
                    new_param_file_list.append(curr_file)
            self.control.set_values('param_file', new_param_file_list)
            # change datafile
            dfile = basename + "_dat.data"
            curr_file = os.path.join(workspace, dfile)
            self.prms.Data.data_file = curr_file
            self.control.set_values('data_file', [curr_file])

            # change mf

            if not (self.mf == None):
                self.mf.change_model_ws(workspace)
                self.mf.name = os.path.join(workspace, basename)
                out_files_list = []
                for out_file in self.mf.output_fnames:
                    ext = out_file.split(".")[-1]
                    if out_file.count('.') > 1:
                        ext = out_file.split(".")
                        del ext[0]
                        ext = ".".join(ext)
                    #new_outfn = os.path.join(workspace, basename + "." + ext)
                    new_outfn =  basename + "." + ext
                    out_files_list.append(new_outfn)
                self.mf.output_fnames = out_files_list

            mfnm = basename + ".nam"
            self.control.set_values('modflow_name', [os.path.join(workspace, mfnm)])

            ## TODO: Update control file
            # update file names in control object
            for rec_name in self.control._gslow_files:
                if rec_name in self.control._record_names:
                    if rec_name in ['modflow_name', 'param_file', 'data_file']:
                        continue
                    file_values = self.control.get_values(rec_name)
                    file_value = []
                    for fil in file_values:
                        dir_name = os.path.dirname(fil)
                        if rec_name == 'modflow_name':
                            mfname = basename + ".nam"
                            filvalue = os.path.join(dir_name, mfname)
                        elif rec_name == 'param_file':
                            continue
                        elif rec_name == 'data_file':
                            continue
                        else:
                            vvfile = rec_name.split("_")
                            del vvfile[-1]
                            vvfile = "_".join(vvfile)
                            if "." in fil:
                                ext = fil.split(".")[-1]
                            else:
                                ext = "dat"
                            vvfile = basename + "_" + vvfile + "." + ext
                            filvalue = os.path.join(workspace, vvfile)

                        file_value.append(filvalue)
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

    def run_model(self):
        fn = self.control_file
        cnt_folder = os.path.dirname(fn)
        fnm = os.path.abspath(fn)
        if not os.path.isfile(self.gsflow_exe):
            print ("Warning : The executable of the model is not specified. Use .gsflow_exe "
                   "to define its path... ")
            return None
        self.__run(exe_name=self.gsflow_exe, namefile=fn)

    def _generate_batch_file(self):
        fn = os.path.dirname(self.control_file)
        fn = os.path.join(fn, "__run_gsflow.bat")
        self.__bat_file = fn
        fidw = open(fn, 'w')
        cmd = self.gsflow_exe + " " + self.control_file
        fidw.write(cmd)
        fidw.close()

    def __run(self, exe_name, namefile, model_ws='./',
              silent=False, pause=False, report=False,
              normal_msg='normal termination',
              async=False, cargs=None):
        """
        This function will run the model using subprocess.Popen.  It
        communicates with the model's stdout asynchronously and reports
        progress to the screen with timestamps

        Parameters
        ----------
        exe_name : str
            Executable name (with path, if necessary) to run.
        namefile : str
            Namefile of model to run. The namefile must be the
            filename of the namefile without the path.
        model_ws : str
            Path to the location of the namefile. (default is the
            current working directory - './')
        silent : boolean
            Echo run information to screen (default is True).
        pause : boolean, optional
            Pause upon completion (default is False).
        report : boolean, optional
            Save stdout lines to a list (buff) which is returned
            by the method . (default is False).
        normal_msg : str
            Normal termination message used to determine if the
            run terminated normally. (default is 'normal termination')
        async : boolean
            asynchonously read model stdout and report with timestamps.  good for
            models that take long time to run.  not good for models that run
            really fast
        cargs : str or list of strings
            additional command line arguments to pass to the executable.
            Default is None
        Returns
        -------
        (success, buff)
        success : boolean
        buff : list of lines of stdout

        """

        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        def which(program):
            fpath, fname = os.path.split(program)
            if fpath:
                if is_exe(program):
                    return program
            else:
                # test for exe in current working directory
                if is_exe(program):
                    return program
                # test for exe in path statement
                for path in os.environ["PATH"].split(os.pathsep):
                    path = path.strip('"')
                    exe_file = os.path.join(path, program)
                    if is_exe(exe_file):
                        return exe_file
            return None

        success = False
        buff = []

        # convert normal_msg to lower case for comparison
        if isinstance(normal_msg, str):
            normal_msg = [normal_msg.lower()]
        elif isinstance(normal_msg, list):
            for idx, s in enumerate(normal_msg):
                normal_msg[idx] = s.lower()

        # Check to make sure that program and namefile exist
        exe = which(exe_name)
        if exe is None:
            import platform
            if platform.system() in 'Windows':
                if not exe_name.lower().endswith('.exe'):
                    exe = which(exe_name + '.exe')
        if exe is None:
            s = 'The program {} does not exist or is not executable.'.format(
                exe_name)
            raise Exception(s)
        else:
            if not silent:
                s = 'pyGSFLOW is using the following executable to run the model: {}'.format(
                    exe)
                print(s)

        if not os.path.isfile(os.path.join(model_ws, namefile)):
            s = 'The namefile for this model does not exists: {}'.format(namefile)
            raise Exception(s)

        # simple little function for the thread to target
        def q_output(output, q):
            for line in iter(output.readline, b''):
                q.put(line)
                # time.sleep(1)
                # output.close()

        # create a list of arguments to pass to Popen
        argv = [exe_name, namefile]

        # add additional arguments to Popen arguments
        if cargs is not None:
            if isinstance(cargs, str):
                cargs = [cargs]
            for t in cargs:
                argv.append(t)

        # run the model with Popen
        self._generate_batch_file()
        argv = self.__bat_file
        model_ws = os.path.dirname(self.control_file)
        proc = sp.Popen(argv,
                        stdout=sp.PIPE, stderr=sp.STDOUT, cwd=model_ws)

        if not async:
            while True:
                line = proc.stdout.readline()
                c = line.decode('utf-8')
                if c != '':
                    for msg in normal_msg:
                        if msg in c.lower():
                            success = True
                            break
                    c = c.rstrip('\r\n')
                    if not silent:
                        print('{}'.format(c))
                    if report == True:
                        buff.append(c)
                else:
                    break
            return success, buff

        # some tricks for the async stdout reading
        q = Queue.Queue()
        thread = threading.Thread(target=q_output, args=(proc.stdout, q))
        thread.daemon = True
        thread.start()

        failed_words = ["fail", "error"]
        last = datetime.now()
        lastsec = 0.
        while True:
            try:
                line = q.get_nowait()
            except Queue.Empty:
                pass
            else:
                if line == '':
                    break
                line = line.decode().lower().strip()
                if line != '':
                    now = datetime.now()
                    dt = now - last
                    tsecs = dt.total_seconds() - lastsec
                    line = "(elapsed:{0})-->{1}".format(tsecs, line)
                    lastsec = tsecs + lastsec
                    buff.append(line)
                    if not silent:
                        print(line)
                    for fword in failed_words:
                        if fword in line:
                            success = False
                            break
            if proc.poll() is not None:
                break
        proc.wait()
        thread.join(timeout=1)
        buff.extend(proc.stdout.readlines())
        proc.stdout.close()

        for line in buff:
            if normal_msg in line:
                print("success")
                success = True
                break

        if pause:
            input('Press Enter to continue...')
        return success, buff
