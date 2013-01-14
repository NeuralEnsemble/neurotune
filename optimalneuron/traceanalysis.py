# -*- coding: utf-8 -*-
"""
Module for mathematical analysis of voltage traces from electrophysiology.

AUTHOR: Mike Vella vellamike@gmail.com

"""
import scipy.stats
import numpy as np
import math

def smooth(x,window_len=11,window='hanning'):
    """Smooth the data using a window with requested size.
    
    This function is useful for smoothing out experimental data.
    This method utilises the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    :param x: the input signal 
    :param window_len: the dimension of the smoothing window; should be an odd integer
    :param window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman', flat window will produce a moving average smoothing.

    :return: smoothed signal
        
    example:

    .. code-block:: python
       
       t=linspace(-2,2,0.1)
       x=sin(t)+randn(len(t))*0.1
       y=smooth(x)
    
    .. seealso::

       numpy.hanning
       numpy.hamming
       numpy.bartlett
       numpy.blackman
       numpy.convolve
       scipy.signal.lfilter
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"

    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')

    edge=window_len/2
    return y[edge:-edge]

def linear_fit(t, y):
    """ Fits data to a line
        
    :param t: time vector
    :param y: variable which varies with time (such as voltage)
    :returns: Gradient M for a formula of the type y=C+M*x
    """

    vals=np.array(y)
    m,C = np.polyfit(t, vals, 1)
    return m


def three_spike_adaptation(t,y):
    """ Linear fit of amplitude vs time of first three AP spikes

    Initial action potential amplitudes may very substaintially in amplitude
    and then settle down.
    
    :param t: time vector (AP times)
    :param y: corresponding AP amplitude
    :returns: Gradient M for a formula of the type y=C+M*x for first three action potentials
    """

    t=np.array(t)
    y=np.array(y)

    t=t[0:3]
    y=y[0:3]
    
    m=linear_fit(t,y)

    return m
    

def exp_fit(t, y):
    """
    Fits data to an exponential.
        
    Returns K for a formula of the type y=A*exp(K*x)
        
    :param t: time vector
    :param y: variable which varies with time (such as voltage)
    
    """

    vals=np.array(y)
    C=np.min(vals)
    vals=vals-C+1e-9 #make sure the data is all positive
    vals = np.log(vals)
    K, A_log = np.polyfit(t, vals, 1)
    return K


def max_min(a,t,delta=0,peak_threshold=0):
    """
    Find the maxima and minima of a voltage trace.
    
    :param a: time-dependent variable (usually voltage)
    :param t: time-vector
    :param delta: the value by which a peak or trough has to exceed its
        neighbours to be considered outside of the noise
    :param peak_threshold: peaks below this value are discarded
        
    :return: turning_points, dictionary containing number of max, min and 
        their locations
        
    .. note::

       minimum value between two peaks is in some ways a better way
       of obtaining a minimum since it guarantees an answer, this may be
       something which should be implemented.
        
    """

    gradients=np.diff(a)
        
    maxima_info=[]
    minima_info=[]
        
    count=0
    
    for i in gradients[:-1]:
        count+=1

        if ((cmp(i,0)>0) & (cmp(gradients[count],0)<0) & (i != gradients[count])):
            #found a maximum
            maximum_value=a[count]
            maximum_location=count
            maximum_time=t[count]
            preceding_point_value=a[maximum_location-1]
            succeeding_point_value=a[maximum_location+1]

            #filter:
            maximum_valid=False #logically consistent but not very pythonic..
            if ((maximum_value-preceding_point_value)>delta)*((maximum_value-succeeding_point_value)>delta):
                maximum_valid=True
            if maximum_value<peak_threshold:
                maximum_valid=False
            if maximum_valid:
                maxima_info.append((maximum_value,maximum_location,maximum_time))
   
    maxima_num=len(maxima_info)
    
    if maxima_num>0:
        minima_num=maxima_num-1
    else:
        minima_num=0
    
    import operator
    
    values_getter=operator.itemgetter(0)
    location_getter=operator.itemgetter(1)
    time_getter=operator.itemgetter(2)
    
    maxima_locations=map(location_getter,maxima_info)
    maxima_times=map(time_getter,maxima_info)
    maxima_values=map(values_getter,maxima_info)

    for i in range(maxima_num-1):
        maximum_0_location=maxima_locations[i]
        maximum_1_location=maxima_locations[i+1]
        
        interspike_slice=a[maximum_0_location:maximum_1_location]
        minimum_value=min(interspike_slice)
        minimum_location=list(interspike_slice).index(minimum_value)+maximum_0_location
        minimum_time=t[minimum_location]
        
        minima_info.append((minimum_value,minimum_location,minimum_time))
   
    minima_locations=map(location_getter,minima_info)
    minima_times=map(time_getter,minima_info)
    minima_values=map(values_getter,minima_info)

    #need to construct the dictionary here:
    turning_points = {'maxima_locations':maxima_locations,'minima_locations':minima_locations,'maxima_number':maxima_num,'minima_number':minima_num,'maxima_times':maxima_times,'minima_times':minima_times, 'maxima_values':maxima_values,'minima_values':minima_values}
    
    return turning_points

def spike_frequencies(t):
    """
    Calculate frequencies associated with interspike times
    
    :param t: a list of spike times in ms
        
    :return: list of frequencies in Hz associated with interspike times and
        times associated with the frequency (time of first spike in pair)
    
    """
    spike_times=np.array(t)
    interspike_times=np.diff(spike_times)
    interspike_frequencies=1000/interspike_times
    
    return [t[:-1],interspike_frequencies]
    
    
def mean_spike_frequency(t):
    """
    Find the average frequency of spikes
    
    :param t: a list of spike times in ms
        
    :return: mean spike frequency in Hz, calculated from mean interspike time
    
    """
    interspike_times=np.diff(t)
    mean_interspike_time=np.mean(interspike_times)
    mean_frequency=1000.0/(mean_interspike_time) #factor of 1000 to give frequency in Hz
    
    if (math.isnan(mean_frequency)):
        mean_frequency=0
    return mean_frequency


def y_from_x(y,x,y_to_find):
    """
    Returns list of x values corresponding to a y after a doing a 
    univariate spline interpolation

    :param x: x-axis numerical data
    :param y: corresponding y-axis numerical data
    :param y_to_find: x value for desired y-value,
        interpolated from nearest two measured x/y value pairs
    
    :return: interpolated y value
    
    """

    from scipy import interpolate

    yreduced = np.array(y) - y_to_find
    freduced = interpolate.UnivariateSpline(x, yreduced, s=3)
    
    return freduced.roots()


def single_spike_width(y,t,baseline):
    """ Find the width of a spike at a fixed height
    
    calculates the width of the spike at height baseline. If the spike shape
    does not intersect the height at both sides of the peak the method
    will return value 0. If the peak is below the baseline 0 will also 
    be returned.
    
    The input must be a single spike or nonsense may be returned.
    Multiple-spike data can be handled by the interspike_widths method.
    
    :param y: voltage trace (array) corresponding to the spike
    :param t: time value array corresponding to y
    :param baseline: the height (voltage) where the width is to be measured.        
    
    :return: width of spike at height defined by baseline

    :think about - set default baseline to none and calculate half-width
    
    """
    try:
        
        value = max(y)
        location = y.index(value)
        
        #moving left:
        while value > baseline:
            location -= 1
            value = y[location]
            undershoot_value = y[location + 1]
            overshoot_time = t[location]
            undershoot_time = t[location + 1]
            interpolated_left_time = np.interp(baseline, [value, undershoot_value], [overshoot_time, undershoot_time])
                            
            if location < 0:
                raise MathsError('Baseline does not intersect spike')
                
        #now go right
        value = max(y)
        location = y.index(value)
        
        while value > baseline :
            location += 1
            value = y[location]
            undershoot_value = y[location - 1]
            overshoot_time = t[location]
            undershoot_time = t[location - 1]
            interpolated_right_time = np.interp(baseline, [value, undershoot_value], [overshoot_time, undershoot_time])
            
            if location > len(y) - 1:
                raise MathsError('Baseline does not intersect spike')

        width = interpolated_right_time - interpolated_left_time
    
    except:
        width = 0
    
    return width


def spike_widths(y,t,baseline=0,delta=0):
    """
    Find the widths of each spike at a fixed height in a train of spikes.
    
    Returns the width of the spike of each spike in a spike train at height 
    baseline. If the spike shapes do not intersect the height at both sides
    of the peak the method will return value 0 for that spike.
    If the peak is below the baseline 0 will also be returned for that spike.
    
    :param y: voltage trace (array) corresponding to the spike train
    :param t: time value array corresponding to y
    :param baseline: the height (voltage) where the width is to be measured.
        
    :return: width of spike at height defined by baseline
    
    """
    
    #first get the max and min data:
    max_min_dictionary=max_min(y,t,delta)
    
    max_num=max_min_dictionary['maxima_number']
    maxima_locations=max_min_dictionary['maxima_locations']
    maxima_times=max_min_dictionary['maxima_times']
    minima_locations=max_min_dictionary['minima_locations']
    maxima_values=max_min_dictionary['maxima_values']
    
    
    spike_widths=[]
    for i in range(max_num):
        #need to splice down the y:
        if i==0:
            left_min_location=0
            right_min_location=minima_locations[i]+1
        elif i==max_num-1:
            left_min_location=minima_locations[i-1]
            right_min_location=len(y)
        else:
            left_min_location=minima_locations[i-1]
            right_min_location=minima_locations[i]+1
        
        spike_shape=y[left_min_location:right_min_location]
        spike_t=t[left_min_location:right_min_location]
        
        try:
            width=single_spike_width(spike_shape,spike_t,baseline)
        except:
            width=0
        
        spike_widths.append(width)
    
    maxima_times_widths=[maxima_times,spike_widths]
    return maxima_times_widths

def burst_analyser(t):
    """ Pearson's correlation coefficient applied to interspike times
        
    :param t: Rank-1 array containing spike times

    :return: pearson's correlation coefficient of interspike times 
    """

    x=np.arange(len(t))
    pearsonr=scipy.stats.pearsonr(x,t)[0]
    return pearsonr

def spike_covar(t):
    """ Calculates the coefficient of variation of interspike times 
        
    :param t: Rank-1 array containing spike times

    :return: coefficient of variation of interspike times 
    """
    
    interspike_times=np.diff(t)
    covar=scipy.stats.variation(interspike_times)
    return covar

def elburg_bursting(spike_times):
    """ bursting measure B as described by Elburg & Ooyen 2004

    :param spike_times: sequence of spike times

    :return: bursting measure B as described by Elburg & Ooyen 2004
    """

    interspikes_1=np.diff(spike_times)

    num_interspikes=len(spike_times)-1

    interspikes_2=[]
    for i in range(num_interspikes-1):
        interspike=interspikes_1[i]+interspikes_1[i+1]
        interspikes_2.append(interspike)

    mean_interspike=np.mean(interspikes_1)    

    var_i_1=np.var(interspikes_1)
    var_i_2=np.var(interspikes_2)

    B=(2*var_i_1-var_i_2)/(2*mean_interspike**2)

    return B

def alpha_normalised_cost_function(value,target,base=10):
    """Fitness of a value-target pair from 0 to 1 
    
    For any value/target pair will give a normalised value for
    agreement 1 is complete value-target match and 0 is 0 match.
    A mirrored exponential function is used.

     .. math:
    :param value: value measured
    :param t: target
    :param base: the base in the expression  :math:'fitness=base**(-x)' where
        :math:'x=x=((value-target)/(target+0.01))**2'
        
    :return: fitness value from 0 to 1
    
    """
    value = float(value)
    target = float(target)
    
    x=((value-target)/(target+0.01))**2 #the 0.01 thing is a bit of a hack at the moment.
    fitness=base**(-x)
    return fitness    

def normalised_cost_function(value,target,Q=None):
    """ Returns fitness of a value-target pair from 0 to 1 
    
        For any value/target pair will give a normalised value for
        agreement 0 is complete value-target match and 1 is "no" match.
        
        If no Q is assigned, it is set such that it satisfies the condition
        fitness=0.7 when (target-valu)e=10*target. This is essentially 
        empirical and seems to work. Mathematical derivation is on Mike Vella's 
        Lab Book 1 p.42 (page dated 15/12/11).
             
    :param value: value measured
    :param t: target
    :param Q: This is the sharpness of the cost function, higher values correspond
        to a sharper cost function. A high Q-Value may lead an optimizer to a solution
        quickly once it nears the solution.
        
    :return: fitness value from 0 to 1
    
    """

    value = float(value)
    target = float(target)
    
    if Q==None:
        Q=7/(300*(target**2))
               
    fitness=1-1/(Q*(target-value)**2+1)
    
    return fitness    

def load_csv_data(file_path,plot=False):
    """
    Return time and voltage data from a csv file
    
    Data must be in a csv and in two columns, first time and second 
    voltage. Units should be SI (Volts and Seconds).

    :param file_path: full file path to file e.g /home/mike/test.csv
        
    :return: two lists - time and voltage

    """
    import csv

    csv_file=file(file_path,'r')
    csv_reader=csv.reader(csv_file)

    v=[]
    t=[]

    i=0
    for row in csv_reader:

        try:

            t_value=float(row[0])*1000 #convert to ms
            v_value=float(row[1])*1000 #convert to mV

            t.append(t_value)
            v.append(v_value)

        except:
            print 'row ',i,' invalid'

        i+=1

    if plot:
        from matplotlib import pyplot        
        pyplot.plot(t,v)
        pyplot.title('Raw data')
        pyplot.xlabel('Time (ms)')
        pyplot.ylabel('Voltage (mV)')
        pyplot.show()

    return t,v


def phase_plane(t,y,plot=False): #plot should be here really
    """
    Return a tuple with two vectors corresponding to the phase plane of
    the tracetarget
    """
    dv=np.diff(y)
    dt=np.diff(t)
    dy_dt=dv/dt

    y=list(y)
    y=y[:-1]

    if plot:
        from matplotlib import pyplot
        pyplot.title('Phase Plot')
        pyplot.ylabel('dV/dt')
        pyplot.xlabel('Voltage (mV)')
        pyplot.plot(y,dy_dt)
        pyplot.show()

    return [y,dy_dt]

def filter(t,v): #still experimental

    import scipy

    fft=scipy.fft(v) # (G) and (H)  
    bp=fft[:]  
    for i in range(len(bp)): # (H-red)  
     if i>=500:bp[i]=0  
    ibp=scipy.ifft(bp) # (I), (J), (K) and (L) 

    return ibp

def pptd(t,y,bins=10,xyrange=None,dvdt_threshold=None,plot=False):
    """
    Returns a 2D map of x vs y data and the xedges and yedges. 
    in the form of a vector (H,xedges,yedges) Useful for the 
    PPTD method described by Van Geit 2007.
    """

    phase_space=phase_plane(t,y)

    #filter the phase space data
    phase_dvdt_new=[]
    phase_v_new=[]
    if dvdt_threshold!=None:
        i=0
        for dvdt in phase_space[1]:
           if dvdt>dvdt_threshold:
               phase_dvdt_new.append(phase_space[1][i])
               phase_v_new.append(phase_space[0][i])
           i+=1
        phase_space[1]=phase_dvdt_new
        phase_space[0]=phase_v_new

    if xyrange!=None:
        density_map=np.histogram2d(phase_space[1], phase_space[0], bins=bins, 
                                normed=False, weights=None)
    elif xyrange==None:
        density_map=np.histogram2d(phase_space[1], phase_space[0], bins=bins, range=xyrange, 
                                normed=False, weights=None)

    #Reverse the density map (probably not necessary as
    #it's being done because imshow has a funny origin):
    density=density_map[0][::-1]
    xedges=density_map[1]
    yedges=density_map[2]

    if plot:
        from matplotlib import pyplot
        extent = [yedges[0], yedges[-1],xedges[0], xedges[-1]]
        imgplot=pyplot.imshow(density, extent=extent)
        imgplot.set_interpolation('nearest') #makes image pixilated
        pyplot.title('Phase Plane Trajectory Density')
        pyplot.ylabel('dV/dt')
        pyplot.xlabel('Voltage (mV)')
        pyplot.colorbar()
        pyplot.show()

    return [density,xedges,yedges]

def spike_broadening(spike_width_list):
    """
    Returns the value of the width of the first AP over
    the mean value of the following APs.
    """

    first_spike=spike_width_list[0]
    mean_following_spikes=np.mean(spike_width_list[1:])
    broadening=first_spike/mean_following_spikes

    return broadening

def pptd_error(t_model,v_model,t_target,v_target,dvdt_threshold=None):
    """
    Returns error function value from comparison of two phase
    pptd maps as described by Van Geit 2007.
    """

    pptd_data=pptd(t_target,v_target,dvdt_threshold=dvdt_threshold)
    target_density_map=pptd_data[0]

    xedges=pptd_data[1]
    xmin=xedges[0]
    xmax=xedges[-1]
    yedges=pptd_data[1]
    ymin=yedges[0]
    ymax=yedges[-1]
    xyrng=[[xmin, xmax], [ymin, ymax]]

    model_density_map=pptd(t_model,v_model,xyrange=xyrng,
                           dvdt_threshold=dvdt_threshold)[0]

    #calculate number of data points for the model and target:
    N_target=sum(sum(target_density_map))
    N_model=sum(sum(model_density_map))

    #normalise each map:
    normalised_target_density_map=target_density_map/float(N_target)
    normalised_model_density_map=model_density_map/float(N_model)

    #calculate the differences and calculate the mod
    difference_matrix=normalised_target_density_map-normalised_model_density_map
    difference_matrix=abs(difference_matrix)
    
    #root each value:
    root_matrix=difference_matrix**0.5

    #sum each element:
    summed_matrix=sum(sum(root_matrix))

    #calculate the error:
    error=summed_matrix**2

    print 'pptd error:'
    print error

    return error

def minima_phases(t,y,delta=0):
    """
    Find the phases of minima.
    
    Minima are found by finding the minimum value between sets of two peaks.
    The phase of the minimum relative to the two peaks is then returned.
    i.e the fraction of time elapsed between the two peaks when the minimum
    occurs is returned.
    
    It is very important to make sure the correct delta is specified for
    peak discrimination, otherwise unexpected results may be returned.
     
    :param y: time-dependent variable (usually voltage)
    :param t: time-vector
    :param delta: the value by which a peak or trough has to exceed its
        neighbours to be considered "outside of the noise"
        
    :return: phase of minimum relative to peaks.
    
    """
    max_min_dictionary=max_min(y,t,delta)
    
    minima_num=max_min_dictionary['minima_number']
    maxima_times=max_min_dictionary['maxima_times']
    minima_times=max_min_dictionary['minima_times']
    maxima_locations=max_min_dictionary['maxima_locations']
    
    minima_phases=[]
    
    for i in range(minima_num):
        maximum_0_t=maxima_times[i]
        maximum_1_t=maxima_times[i+1]
        maximum_0_location=maxima_locations[i]
        maximum_1_location=maxima_locations[i+1]
        minimum_time=minima_times[i]
        phase=(minimum_time-maximum_0_t)/(maximum_1_t-maximum_0_t)
        minima_phases.append(phase)
        
    phase_list=[minima_times,minima_phases]
    
    return phase_list
    
    
class TraceAnalysis(object):
    """
    Base class for analysis of electrophysiology data

    Constructor for TraceAnalysis base class takes the following arguments:
       
    :param v: time-dependent variable (usually voltage)
    :param t: time-array (1-to-1 correspondence with v-array)
    :param start_analysis: time in v,t where analysis is to start
    :param end_analysis: time in v,t where analysis is to end
    """
    
    def __nearest_index(self,
			array,
			target_value):

        """Finds index of first nearest value to target_value in array"""
        nparray=np.array(array)
        differences=np.abs(nparray-target_value)
        min_difference=differences.min()
        index=np.nonzero(differences==min_difference)[0][0]
        return index
        
    def __init__(self,v,t,start_analysis=0,end_analysis=None):

        self.v=v
        self.t=t
        
        start_index=self.__nearest_index(self.t,start_analysis)
        end_index=self.__nearest_index(self.t,end_analysis)
        
        if end_analysis!=None:            
            self.v=v[start_index:end_index]
            self.t=t[start_index:end_index]
            
    def plot_trace(self,
		   save_fig=False,
		   trace_name='voltage_trace.png',
		   show_plot=True):
	"""
	Plot the trace and save it if requested by user.
	"""
	
        import matplotlib.pyplot as plt
        
        plt.plot(self.t,self.v)
        if save_fig:
            plt.savefig(trace_name)
        
        if show_plot:
            plt.show()
                
    def evaluate_fitness(self,
			 target_dict={},
			 target_weights=None,
			 cost_function=normalised_cost_function):
	"""
	Return the estimated fitness of the data, based on the cost function being used.

	:param target_dict: key-value pairs for targets
	:param target_weights: key-value pairs for target weights
	:param cost_function: cost function (callback) to assign individual targets sub-fitness.
	"""

        #calculate max fitness value (TODO: there may be a more pythonic way to do this..)
        worst_cumulative_fitness=0
        for target in target_dict.keys():
            if target_weights==None: 
                target_weight=1
            else:
                target_weight=target_weights[target]
                
            worst_cumulative_fitness+=target_weight
    
        #if we have 1 or 0 peaks we won't conduct any analysis
        if self.analysable_data==False:
            print 'data is non-analysable'
            return worst_cumulative_fitness
            
        else:
            fitness=0
        
            for target in target_dict.keys():
            
                target_value=target_dict[target]
                print 'examining target '+target
                if target_weights==None: 
                    target_weight=1
                else:
                    target_weight=target_weights[target]
                
                value=self.analysis_results[target]
                #let function pick Q automatically
                fitness+=target_weight*cost_function(value,target_value)
                
            self.fitness=fitness
            return self.fitness
            
class IClampAnalysis(TraceAnalysis):
    """Analysis class for data from whole cell current injection experiments

    This is designed to work with simulations of spiking cells.

    :param v: time-dependent variable (usually voltage)
    :param t: time-vector
    :param analysis_var: dictionary containing parameters to be used
        in analysis such as delta for peak detection
    :param start_analysis: time t where analysis is to start
    :param end_analysis: time in t where analysis is to end
       
    """
        
    def __init__(self,v,
		 t,
		 analysis_var,
		 start_analysis=0,
		 end_analysis=None,
		 target_data_path=None,
		 smooth_data=False,
		 show_smoothed_data=False,
		 smoothing_window_len=11):

        #call the parent constructor to prepare the v,t vectors:
        super(IClampAnalysis,self).__init__(v,t,start_analysis,end_analysis)

        if smooth_data == True:
                self.v=smooth(self.v,window_len=smoothing_window_len)

	if show_smoothed_data == True:
	    from matplotlib import pyplot
	    pyplot.plot(self.t,self.v)
	    pyplot.show()

        self.delta=analysis_var['peak_delta']
        self.baseline=analysis_var['baseline']
        self.dvdt_threshold=analysis_var['dvdt_threshold']

        self.target_data_path=target_data_path

	try:
	    peak_threshold = analysis_var["peak_threshold"]
	except:
	    peak_threshold = None
        self.max_min_dictionary=max_min(self.v,self.t,self.delta,
					peak_threshold = peak_threshold)
        
        max_peak_no=self.max_min_dictionary['maxima_number']
        
        if max_peak_no<3:
            self.analysable_data=False
        else:
            self.analysable_data=True
            
    def analyse(self):
        """If data is analysable analyses and puts all results into a dict"""    
        
        if self.analysable_data:
            max_min_dictionary=self.max_min_dictionary
            analysis_results={}

            analysis_results['average_minimum'] = np.average(max_min_dictionary['minima_values'])
            analysis_results['average_maximum'] = np.average(max_min_dictionary['maxima_values'])
            analysis_results['min_peak_no'] = max_min_dictionary['minima_number']
            analysis_results['max_peak_no'] = max_min_dictionary['maxima_number']
            analysis_results['mean_spike_frequency'] = mean_spike_frequency(max_min_dictionary['maxima_times'])
            analysis_results['interspike_time_covar'] = spike_covar(max_min_dictionary['maxima_times'])
            analysis_results['first_spike_time'] = max_min_dictionary['maxima_times'][0]
            trough_phases=minima_phases(self.t,self.v,delta = self.delta)
            analysis_results['trough_phase_adaptation'] = exp_fit(trough_phases[0],trough_phases[1])
            spike_width_list=spike_widths(self.v,self.t,self.baseline,self.delta)
            analysis_results['spike_width_adaptation'] = exp_fit(spike_width_list[0],spike_width_list[1])
            spike_frequency_list = spike_frequencies(max_min_dictionary['maxima_times'])
            analysis_results['peak_decay_exponent'] = three_spike_adaptation(max_min_dictionary['maxima_times'],max_min_dictionary['maxima_values'])
            analysis_results['trough_decay_exponent'] = three_spike_adaptation(max_min_dictionary['minima_times'],max_min_dictionary['minima_values'])
            analysis_results['spike_frequency_adaptation'] = exp_fit(spike_frequency_list[0],spike_frequency_list[1])
            analysis_results['spike_broadening'] = spike_broadening(spike_width_list[1])
	    analysis_results['peak_linear_gradient'] = linear_fit(max_min_dictionary["maxima_times"],max_min_dictionary["maxima_values"])


            #this line here is because PPTD needs to be compared directly with experimental data:
            if self.target_data_path!=None:
                t_experimental,v_experimental=load_csv_data(self.target_data_path)
                try:
                    analysis_results['pptd_error']=pptd_error(self.t,self.v,
                                              t_experimental,v_experimental,
                                              dvdt_threshold=self.dvdt_threshold)
                except:
                    print 'WARNING PPTD failure'
                    analysis_results['pptd_error'] = 1

            self.analysis_results=analysis_results

        else:
            print 'data not suitable for analysis,<3 APs'
