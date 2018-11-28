import os
import pandas as pd
import supports
import datetime
import numpy as np
class Prms_data(object):
    def __init__(self, data_file = None, data_df = None ):
        self.data_file = data_file
        self.data_df = data_df
        self.data_names =  ['tmax', 'tmin', 'precip', 'runoff', 'pan_evap', 'solrad', 'from_data', 'rain_day']

        if (data_df is None) and (not(data_file is None)) :
           self.from_file()

        if (data_df is None) and data_file is None :
            print(" Warning: This is empty data object")


    def from_file(self):
        data_file = self.data_file
        data_items = ['tmax', 'tmin', 'precip', 'runoff', 'pan_evap', 'solrad', 'from_data', 'rain_day']
        fid = open(data_file, 'r')
        self.headers = fid.readline().strip()
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
                    columns.append(val_nm[0] + "_" + str(val))
        columns = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'] + columns
        data_pd =  pd.read_csv(fid, delim_whitespace=True, names=columns)
        Dates = []
        for index, irow in data_pd.iterrows():
            dt = datetime.datetime(year=int(irow['Year']), month= int(irow['Month']), day= int(irow['Day']),
                                   hour=int(irow['Hour']),
                              minute= int(irow['Minute']), second= int(irow['Second']))
            Dates.append(dt)

        data_pd['Date'] = Dates
        fid.close()
        self.data_df = data_pd

    def write(self):
        fid = open(self.data_file, 'w')
        fid.write(self.headers)
        fid.write("\n")
        columns = self.data_df.columns
        climate_data = []
        climate_count = {}
        climate_unique = []
        for col in columns:
            nm = col.split("_")[0]
            if nm in self.data_names:
                climate_data.append(nm)
                if not (nm in climate_unique):
                    climate_unique.append(nm)
                if nm in climate_count.keys():
                    climate_count[nm] = climate_count[nm] + 1
                else:
                    climate_count[nm] = 1




        # write headers
        for clim_name in climate_unique:
            line = clim_name + " " + str(climate_count[clim_name]) + "\n"
            fid.write(line)
        fid.write("#########################################################################\n")
        pd_to_write = self.data_df.copy()
        pd_to_write = pd_to_write.drop(['Date'], axis=1)
        pd_to_write.to_csv(fid, index = False, sep =" ", header = False)







        fid.close()
        pass
