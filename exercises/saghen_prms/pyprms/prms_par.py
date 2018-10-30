
# this function will read a record for a parameter
class prms_par(object):
    def __init__(self):
        types = {'int':1, 'real':2, 'double':3, 'string':4}
        self.name = None
        self.width = 10 # in gsflow, this value does not exist
        self.no_dimensions = None
        self.dimension_names = ['None'] # example is 2d array nhru by nmonths
        self.no_values = None
        self.value_type = None
        self.values = []

    def read_param(self, par_dict):
            self.no_dimensions = int(par_dict[0])
            self.dimension_names = par_dict[1]
            self.no_values = int(par_dict[2])
            self.value_type = int(par_dict[3])
            self.values = par_dict[4]


    def write_param(self, fn):
        pass

    def plot_param(self):
        pass

