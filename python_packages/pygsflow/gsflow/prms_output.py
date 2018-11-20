from control import Control
import pandas as pd
import datetime
import matplotlib.pyplot as plt

class Statistics(object):
    def __init__(self, control = None):
        if control == None:
            raise ValueError("Control file is not loaded...")

        statVar_file = control.get_values("stat_var_file")[0]
        statvar_flg = control.get_values("statsON_OFF")[0]
        if statvar_flg == 0:
            print("There is no statvar output since statsON_OFF = 0 ")
            return None

        self.statvar_file = statVar_file
        self.statvar_names = control.get_values("statVar_names")
        self.statvar_elements = control.get_values("statVar_element")

        self._load_statvar_file()

    def _load_statvar_file(self):
        print ("Loading the statvar output file .....")
        fid = open(self.statvar_file, 'r')
        nvals = int(fid.readline().strip())
        var_names = []
        var_element = []
        for header in range(nvals):
            nm, elem = fid.readline().strip().split()
            nm = nm + "_" + elem
            var_names.append(nm)
            var_element.append(int(elem))

        columns = ['ID', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'] + var_names
        stat_df = pd.read_csv(fid, delim_whitespace=True, names=columns)
        Dates = []
        for index, irow in stat_df.iterrows():
            dt = datetime.datetime(year=int(irow['Year']), month=int(irow['Month']), day=int(irow['Day']),
                                   hour=int(irow['Hour']),
                                   minute=int(irow['Minute']), second=int(irow['Second']))
            Dates.append(dt)

        stat_df['Date'] = Dates
        self.stat_df = stat_df
        fid.close()
        print ("Finished Load the statvar output file .....")


    def plot(self):
        for i, name in enumerate(self.statvar_names):
            nm = name + "_" + self.statvar_elements[i]
            self.stat_df.plot(x = 'Date', y = nm)





