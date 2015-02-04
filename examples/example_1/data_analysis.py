from pyelectro import analysis as pye_analysis
from matplotlib import pyplot

file_name = '100pA_1.csv'
t,v=pye_analysis.load_csv_data(file_name)

analysis_var={'peak_delta':0.1,'baseline':0,'dvdt_threshold':2,'peak_threshold':0}

analysis=pye_analysis.IClampAnalysis(v,
                                     t,
                                     analysis_var,
                                     start_analysis=150,
                                     end_analysis=900)

res = analysis.analyse()

print res

pyplot.plot(t,v)
pyplot.suptitle('Data read in from: %s'%file_name)
pyplot.show()
