from nrndev import nrnanalysis as nanalysis
from matplotlib import pyplot

t,v=nanalysis.load_csv_data('/home/mike/dev/diego/data/100pA_1.csv')
analysis=nanalysis.IClampAnalysis

analysis_var={'peak_delta':1,'baseline':0,'dvdt_threshold':2}

analysis=nanalysis.IClampAnalysis(v,t,analysis_var,start_analysis=150,end_analysis=900)

analysis.analyse()

pyplot.plot(t,v)
pyplot.show()
