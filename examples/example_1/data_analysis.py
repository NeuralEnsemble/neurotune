from pyelectro import analysis as pye_analysis
from matplotlib import pyplot

t,v=pye_analysis.load_csv_data('100pA_1.csv')

analysis_var={'peak_delta':1,'baseline':0,'dvdt_threshold':2}

analysis=pye_analysis.IClampAnalysis(v,t,analysis_var,start_analysis=150,end_analysis=900)

res = analysis.analyse()

pyplot.plot(t,v)
pyplot.show()
