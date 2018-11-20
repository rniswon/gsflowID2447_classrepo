from __future__ import (absolute_import, division, print_function)
import os
import numpy as np
import copy



class Control(object):
    """
    Class to hold information about control file, also it reads and writes data.
    """

    def __init__(self, records_list=None, control_file='temp_cont.control'):
        """

        :param control_file:
        :param control_dict:
        :param control_list:
        """
        #TODO : Fix data type forceing
        self._gslow_files = ['csv_output_file', 'data_file', 'gsflow_output_file',
                             'model_output_file', 'modflow_name', 'param_file', 'stat_var_file',
                             'var_init_file', 'var_save_file',
                             'ani_output_file', 'mapOutVar_names', 'param_print_file', 'stats_output_file']

        self.headers = ["Control File"]
        if not (records_list == None):
            self.control_file = control_file
            self.records_list = records_list

        elif os.path.isfile(control_file):
            self.control_file = control_file
            self.from_file()

        else:
            self.records_list = None
            self.control_file = control_file
        # get record names
        self._record_names = []
        if not (self.records_list == None):
            self._records_list = copy.deepcopy(self.records_list)
            for rec in self._records_list:
                self._record_names.append(rec.name)

        self._make_pths_abs()
    # @property
    # def record_list(self):
    #     return self.__values
    #
    # @record_list.setter
    # def record_list(self, record_list):
    #     self.__record_list = record_list

    def from_file(self, filename = None):
        # todo: msg
        if filename:
            fn = filename
        else:
            fn = self.control_file
        if not (os.path.isfile(self.control_file)):
            raise ValueError("Invalid file name ....")

        fid = open(fn, 'r')
        content = fid.readlines()
        fid.close()
        content = content.__iter__()

        headers = []
        records_list = []
        control_field_order = []
        EndOfFile = False
        _read_comments = True
        while True:
            if EndOfFile:
                break
            record = content.next().strip()
            # read comments
            if _read_comments:
                if "####" in record:
                    _read_comments = False
                    continue
                headers.append(record)
                continue


            # read records information
            field_name = record
            nvalues = int(content.next().strip())
            data_type = int(content.next().strip())
            values = []

            # loop over values
            while True:
                try:
                    record = content.next().strip()
                    if record == '':
                        continue  # empty line
                except:  # end of the file
                    EndOfFile = True
                    curr_record = Control_record(name=field_name, values=values, datatype=data_type, nvalues=nvalues)
                    records_list.append(curr_record)
                    break

                if "####" in record:
                    curr_record = Control_record(name=field_name, values=values, datatype=data_type, nvalues=nvalues)
                    records_list.append(curr_record)
                    break
                else:
                    values.append(record)
        self.headers = headers
        self.records_list = records_list


    def _make_pths_abs(self):
        for file in self._gslow_files:
            if file in self._record_names:
                gs_fn = self.get_values(file)
                flist = []
                for ff in gs_fn:
                    abs_file = self._get_file_abs(control_file = self.control_file, fn = ff)
                    flist.append(abs_file)
                self.set_values(file, flist)

    def _get_file_abs(self, control_file=None, fn=None):
        control_folder = os.path.dirname(control_file)
        abs_file = os.path.abspath(os.path.join(control_folder, fn))
        return abs_file

    def _generate_attributes(self):
        self.records_list
        for rec in self.records_list:
            setattr(self, rec.name, rec)

    def get_record(self, name):
        """
        Get a complete record object
        :return:
        """
        record = None
        if len(self.records_list) > 0:
            for rec in self.records_list:
                if rec.name == name:
                    record = rec
                    break
        else:
            print("Control Object is empty....")
            return None

        if isinstance(record, Control_record):
            return record
        else:
            print("The record does not exist...")
            return None

    def get_values(self, name):
        """
                Get a complete record object
                :return:
                """
        values = None
        if len(self.records_list) > 0:
            for rec in self.records_list:
                if rec.name == name:
                    values = rec.values
                    break
        else:
            print("Control Object is empty....")
            return None

        if isinstance(values, np.ndarray):
            return values
        else:
            print("The values does not exist...")
            return None

    def set_values(self, name, values):
        """
                Get a complete record object
                :return:
                """

        if len(self.records_list) > 0:
            for rec in self.records_list:
                if rec.name == name:
                    rec.values = np.array(values)
                    return
        else:
            print("Control Object is empty....")
            return None



    def get_record_names(self):
        return self._record_names

    def add_record(self, name=None, values=None, where=None, after=None):
        if isinstance(name, str):
            pass
        else:
            raise ValueError("Record name must be string")
        if isinstance(values, list) or isinstance(values, np.ndarray):
            pass
        else:
            raise ValueError("Record name must be string")
        if name in self._record_names:
            print("The record already exist...")
            return

        new_record = Control_record(name=name, values=values)

        if after:
            for index, recc in enumerate(self._record_names):
                if recc == after:
                    break;
            self._record_names.insert(index + 1, name)
            self.records_list.insert(index + 1, new_record)
            return

        if where:
            self._record_names.insert(where, name)
            self.records_list.insert(where, new_record)
        else:
            self._record_names = self._record_names + [name]
            self.records_list = self.records_list + [new_record]

    def remove_record(self, name):
        if isinstance(name, str):
            pass
        else:
            raise ValueError("Record name must be string")

        if name not in self._record_names:
            print("The record does not exist...")
            return

        for index, nm in enumerate(self._record_names):
            if nm == name:
                del self._record_names[index]
                del self.records_list[index]
                return

    def write(self, file = None):
        # make sure files are correct
        #self._make_pths_abs()
        if not (file == None):
            filename = file
        else:
            filename = self.control_file
        fid = open(filename, 'w')
        for iline, header in enumerate(self.headers):
            if iline == 0:
                txt = header.strip()
            else:
                txt = "\n" + header.strip()
            fid.write(txt)

        for record in self.records_list:
            record.write(fid)
        fid.write("\n")
        fid.close()


class Control_record(object):
    def __init__(self, name=None, values=None, datatype=None, nvalues=None):
        """

        :param name: string for field name
        :param values: list or numpy array
        :param datatype:
        :param nvalues:
        """

        self.DATA_TYPES_options = {1: 'integer', 2: 'real', 3: 'double', '4': 'string'}
        # record name
        if isinstance(name, str):
            self.name = name
        else:
            raise ValueError("Generate an error, name of the record ( {} ) is not a string".format(name))

        # record values
        self.__values = values
        self._check_values(values)


        # number of values
        if nvalues:
            self.nvalues = nvalues
            if len(values) != nvalues:
                print("Warning, number of values in not {} is compatable with values assigned, the number of "
                      "values is changed".format(name))
                self.nvalues = len(values)
        else:
            self.nvalues = len(values)

        if datatype:
            self.datatype = datatype
        else:
            print("Warning: data type will be infered from data supplied")
            if 'float' in self.__values.dtype.name:
                self.datatype = 2
            elif 'int' in self.__values.dtype.name:
                self.datatype = 1
            elif 'string' in self.__values.dtype.name:
                self.datatype = 4
            else:
                raise ValueError("Value type is not recognized...{}", self.values.dtype)

        self._force_data_type()

    def _check_values(self, values):
        if isinstance(values, np.ndarray):
            self.__values = values
        elif isinstance(values, list):
            try:
                values = np.array(values)
                self.__values = values
                pass
            except:
                raise ValueError("Cannot convert the list to 1D numpy array ")
        else:
            raise ValueError("Values must be list or 1D numpy array ")
        pass



    def _force_data_type(self):
        """ make sure that the datatype is consisitent with used type"""
        self.__values

        if self.datatype == 1:
            self.__values = self.__values.astype(int)
        elif self.datatype == 2 or self.datatype == 3:
            self.__values = self.__values.astype(float)
        elif self.datatype == 4:
            self.__values = self.__values.astype(str)
        else:
            raise ValueError("Value type is not recognized...{}", self.values.dtype)

    @property
    def values(self):
        self._force_data_type()
        return self.__values

    @values.setter
    def values(self, values):
        self.__values = values
        self._check_values(values)

        if len(values) != self.nvalues:
            self.nvalues = len(values)
            print("Warning: the number of values is modefied")
        # change data type
        self._check_dtype()
        self._force_data_type()

    def _check_dtype(self):
        if 'float' in self.__values.dtype.name:
            self.datatype = 2
        elif 'int' in self.__values.dtype.name:
            self.datatype = 1
        elif 'string' in self.__values.dtype.name:
            self.datatype = 4
        else:
            raise ValueError("Value type is not recognized...{}", self.values.dtype)

    def write(self, fid):
        fid.write("\n")
        fid.write("####")
        fid.write("\n")
        fid.write(self.name)

        # write nvalues
        fid.write("\n")
        fid.write(str(self.nvalues))

        # write datatype
        fid.write("\n")
        fid.write(str(self.datatype))

        # write values
        for val in self.values:
            fid.write("\n")
            fid.write(str(val))

    def __repr__(self):
        try:
            return self.name
        except:
            return "control Record"

    def __str__(self):
        print_str = ""
        print_str = print_str + "\n"
        print_str = print_str + "####"
        print_str = print_str + "\n"
        print_str = print_str + self.name
        print_str = print_str + "\n"
        print_str = print_str + str(self.nvalues)
        print_str = print_str + "\n"
        print_str = print_str + str(self.datatype)

        # write values
        for i, val in enumerate(self.values):
            if i > 3:
                print_str = print_str + ".\n.\n."
                break
            print_str = print_str + "\n"
            print_str = print_str + str(val)

        print_str = print_str + "\n"
        print_str = print_str + "####"
        return print_str

        pass
    def from_dict(self):
        pass

    def to_dict(self):
        pass
