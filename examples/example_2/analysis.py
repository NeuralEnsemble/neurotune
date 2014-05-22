from pyelectro import io
from pyelectro import analysis
from matplotlib import pyplot as plt

t,v=io.load_csv_data('./100pA_1.csv')

analysis_var={'peak_delta':1,'baseline':0,'dvdt_threshold':2}

analysis=analysis.IClampAnalysis(v,
                                 t,
                                 analysis_var,
                                 start_analysis=150,
                                 end_analysis=900,
                                 smooth_data=True,
                                 show_smoothed_data=True)

analysis.analyse()

print analysis.analysable_data
print analysis.analysis_results

plt.xlabel('Time (ms)')
plt.ylabel('Membrane potential (mV)')
plt.grid('on')

plt.plot(t,v)
plt.show()
