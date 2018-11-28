import os
import numpy as np
from control import Control as Cont
from parameter import Parameters as Param
from prms_data import Prms_data
from prms_output import Statistics
import supports


class Prms(object):
    def __init__(self, control=None, parameters=None, control_file=None):

        if isinstance(control, Cont):
            self.control = control
            self._control_file = control.control_file
        else:
            print("Control info. will be read from a file ...")
            self.control = control

        if isinstance(parameters, Param):
            self.parameters = parameters
        else:
            print("Parameters will be read from a file/ files...")
            self.parameters = parameters
        self.load()

    def load(self):
        # load control information
        if not(self.control_file == None):
            self.control = Cont(control_file=self.control_file)
        else:
            raise ValueError("Error: cannot load becuase the control file does not exit")

        # load parameters
        abs_files = []
        parm_files = self.control.get_values('param_file')
        #for ffn in parm_files:
            #f = supports._get_file_abs(control_file=self.control_file, fn=ffn)
        #    abs_files.append(f)
        self.parameters = Param(parameter_files=parm_files)

        # load data
        data_file = self.control.get_values('data_file')
        #data_file = supports._get_file_abs(control_file=self.control_file, fn=data_file[0])
        self.Data = Prms_data(data_file=data_file)

        print ("Prms model is loaded .....")

    def get_statVar(self):
        self.stat = Statistics(control = self.control)
        return self.stat.stat_df

    @property
    def control_file(self):
        return self._control_file

    @control_file.setter
    def control_file(self, new_values):
        self._control_file = new_values
        self.control.control_file = self._control_file




