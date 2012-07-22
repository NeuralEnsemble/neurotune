#===============================================================================
# version 0.3 last modifification 14/7/11
# Author: Mike Vella
#===============================================================================

from neuron import h
import neuron
import numpy as np


def geom_nseg(section,f=100):
    
    """
    Python version of the same function as on p.123 of The Neuron Book
    """

    L=section.L
    
    h.load_func('lambda_f')
    nseg=int((L/(0.1*h.lambda_f(f,sec=section))+0.9)/2)*2+1
	
    return nseg

class Simulation(object):

    """
    Simulation class mainly taken from Philipp Rautenberg, this class has been
    modified slightly by Mike Vella to accept a section rather than a cell as the 
    object passed to the set_IClamp method of the class.
    see http://www.paedia.info/neuro/intro_pydesign.html

    Objects of this class control a current clamp simulation. Example of use:
    >>> cell = Cell()
    >>> sim = Simulation(cell)
    >>> sim.go()
    >>> sim.show()
    """

    def __init__(self, recording_section, sim_time=1000, dt=0.05, v_init=-60):

        #h.load_file("stdrun.hoc") # Standard run, which contains init and run
        self.recording_section = recording_section
        self.sim_time = sim_time
        self.dt = dt
        self.go_already = False
        self.v_init=v_init

    def set_VClamp(self,dur1=100,amp1=0,dur2=0,amp2=0,dur3=0,amp3=0,):
        """
        Initializes values for a Voltage clamp.

        techincally this is an SEClamp in neuron, which is a
        three-stage current clamp.
        """
        stim = neuron.h.SEClamp(self.recording_section(0.5))
        
        stim.rs=0.1
        stim.dur1 = dur1
        stim.amp1 = amp1
        stim.dur2 = dur2
        stim.amp2 = amp2
        stim.dur3 = dur3
        stim.amp3 = amp3

        self.Vstim = stim
    def set_IClamp(self, delay=5, amp=0.1, dur=1000):
        """
        Initializes values for current clamp.
        
        Default values:
          
          delay = 5 [ms]
          amp   = 0.1 [nA]
          dur   = 1000 [ms]
        """
        stim = neuron.h.IClamp(self.recording_section(0.5))
        stim.delay = delay
        stim.amp = amp
        stim.dur = dur
        self.stim = stim

    def show(self):
        from matplotlib import pyplot as plt
        if self.go_already:
            x = np.array(self.rec_t)
            y = np.array(self.rec_v)
            plt.plot(x, y)
            #plt.title("Hello World")
            plt.xlabel("Time [ms]")
            plt.ylabel("Voltage [mV]")
            #plt.axis(ymin=-120, ymax=-50)
        else:
            print("""First you have to `go()` the simulation.""")
        plt.show()
    
    def set_recording(self):
        # Record Time
        self.rec_t = neuron.h.Vector()
        self.rec_t.record(neuron.h._ref_t)
        # Record Voltage
        self.rec_v = neuron.h.Vector()
        self.rec_v.record(self.recording_section(0.5)._ref_v)

    def get_recording(self):
        time = np.array(self.rec_t)
        voltage = np.array(self.rec_v)
        return time, voltage

    def go(self, sim_time=None):
        self.set_recording()
        neuron.h.dt = self.dt
        #neuron.h.finitialize(h.E)
        
        neuron.h.finitialize(self.v_init)
        neuron.init()
        if sim_time:
            neuron.run(sim_time)
        else:
            neuron.run(self.sim_time)
        self.go_already = True

    def get_tau_eff(self, ip_flag=False, ip_resol=0.01):
        time, voltage = self.get_recording()
        vsa = np.abs(voltage - voltage[0]) #vsa: voltage shifted and absolut
        v_max = np.max(vsa)
        exp_val = (1 - 1 / np.exp(1)) * v_max # 0.6321 * v_max
        ix_tau = np.where(vsa > (exp_val))[0][0] 
        tau = time[ix_tau] - self.stim.delay 
        return tau
  
    def get_Rin(self):
        """
        This function returnes the input resistance.
        """
        _, voltage = self.get_recording()
        volt_diff = max(voltage) - min(voltage)
        Rin = np.abs(float(volt_diff / self.stim.amp))
        return Rin

def record(seg,variable):
    """
    Records a variable in a section easily.

    The variable must obey the standard neuron convention,
    for instance - to record a gating variable n from a
    mechanism kv (i.e SUFFIX kv set in mod file) then variable
    should be a string "n_kv".    
    """

    vec=neuron.h.Vector()
    variable='_ref_'+variable
    vec.record(getattr(seg,variable))
    data_array=np.array(vec)
    return vec

def grand(sigma):
    import random

    random_number=abs(random.gauss(1.0,sigma))
    return random_number


class __Cell(object):
    """Base class for neurons cells"""

    def seclist(self,regionlist):

        secs=[]
        for region in regionlist:
            sec=region.all_sections
            secs+=sec
        return secs

    def dendrite_list(self,num_dends=3,bifurcations=1,root_L=100,term_L=10,
                     L_sigma=0.0,root_d=5,term_d=5,branch_prob=1.0):
        
        dendrites=[]
        for i in range(num_dends):
            init_sec_L=root_L
            dend=DendriticTree(bifurcations=bifurcations,root_L=root_L,term_L=term_L,
                              L_sigma=L_sigma,root_d=root_d,term_d=term_d,
                              branch_prob=branch_prob)
            
            dendrites.append(dend)

        return dendrites

class CA1Basket(__Cell):

    """
    Loosely-based on Sarga et al. 2006
    """
    def __init__(self,somatic_dendrites=4,bifurcations=2,
                L_sigma=0.0,branch_prob=1.0,
		soma_L=17.0,soma_d=17.0,
                dendritic_root_L=150.0,dendritic_root_d=2.0,
                dendritic_term_L=80.0,dendritic_term_d=1.0):

        import random
        import math

        soma=Soma(diam=soma_d,length=soma_L)

        #make the somatic denrites

        somatic_dends=self.dendrite_list(num_dends=somatic_dendrites,
                bifurcations=bifurcations,root_L=dendritic_root_L,
                term_L=dendritic_term_L,L_sigma=L_sigma,
                root_d=dendritic_root_d,term_d=dendritic_term_d,
                branch_prob=branch_prob)
        
        #connect dendrites to soma:
        for dend in somatic_dends:
            dendsec=dend.get_connecting_section()
            soma.connect(dendsec,region_end=random.random()) #for now connecting randomly but need to do this on some linspace
        
        #assign public sections
        self.soma_sections=[soma.body]
        self.soma_body=soma.body
        self.somatic_dendrites=self.seclist(somatic_dends)
        self.dendrites=self.somatic_dendrites
        self.all_sections=self.dendrites+[self.soma_body]

        #ensure enough segments are created:

        for sec in self.all_sections:
            sec.nseg=5*geom_nseg(sec,f=200)

class LayerV(__Cell):

    def __init__(self,somatic_dendrites=20,oblique_dendrites=6,
                somatic_bifurcations=2,apical_bifurcations=4,oblique_bifurcations=2,
                L_sigma=0.0,apical_branch_prob=1.0,
            	somatic_branch_prob=1.0,oblique_branch_prob=1.0,
                soma_L=30.0,soma_d=25.0,axon_segs=5.0,myelin_L=100.0,
                apical_root_L=400.0,oblique_root_L=150.0,somadend_root_L=150.0,
                apical_term_L=100.0,oblique_term_L=30.0,somadend_term_L=30.0,
                apical_root_d=5.0,oblique_root_d=1.0,somadend_root_d=1.0,
                apical_term_d=0.5,oblique_term_d=0.35,somadend_term_d=0.35):

        import random
        import math

        #make main the regions:
        if axon_segs!=0:
            axon=Axon(n_axon_seg=axon_segs)
	
        soma=Soma(diam=soma_d,length=soma_L)

        main_apical_dendrite=DendriticTree(bifurcations=
                apical_bifurcations,root_L=apical_root_L,
                term_L=apical_term_L,L_sigma=L_sigma,
                root_d=apical_root_d,term_d=apical_term_d,
                branch_prob=apical_branch_prob)

        #make the somatic denrites

        somatic_dends=self.dendrite_list(num_dends=somatic_dendrites,
                bifurcations=somatic_bifurcations,root_L=somadend_root_L,
                term_L=somadend_term_L,L_sigma=L_sigma,
                root_d=somadend_root_d,term_d=somadend_term_d,
                branch_prob=somatic_branch_prob)


        #make oblique dendrites:

        oblique_dends=self.dendrite_list(num_dends=oblique_dendrites,
                bifurcations=oblique_bifurcations,root_L=oblique_root_L,
                term_L=oblique_term_L,L_sigma=L_sigma,
                root_d=oblique_root_d,term_d=oblique_term_d,
                branch_prob=oblique_branch_prob)

        #connect axon to soma:
        axon_section=axon.get_connecting_section()
        self.soma_body=soma.body
        soma.connect(axon_section,region_end=1)
        
        #connect apical dendrite to soma:
        apical_dendrite_firstsec=main_apical_dendrite.get_connecting_section()
        soma.connect(apical_dendrite_firstsec,region_end=0)

        #connect oblique dendrites to apical first section:
        for dendrite in oblique_dends:
	        apical_location=math.exp(-5*random.random()) #for now connecting randomly but need to do this on some linspace
	        apsec=dendrite.get_connecting_section()
	        apsec.connect(apical_dendrite_firstsec,apical_location,0)

        #connect dendrites to soma:
        for dend in somatic_dends:
            dendsec=dend.get_connecting_section()
            soma.connect(dendsec,region_end=random.random()) #for now connecting randomly but need to do this on some linspace
        
        #assign public analysis properties
        self.apical_bc_asymmetry=main_apical_dendrite.bc_asymmetry()
#        self.apical_bifib1_asymmetry=main_apical_dendrite.bifib1_asymmetry()
        self.apical_children_areas=main_apical_dendrite.children_areas()
        self.distance_scaled_area=main_apical_dendrite.distance_scaled_area()
        self.scaled_bc_asymmetry=main_apical_dendrite.scaled_bc_asymmetry()

        #assign public sections
        self.axon_iseg=axon.iseg
        self.axon_hill=axon.hill
        self.axon_nodes=axon.nodes
        self.axon_myelin=axon.myelin
        self.axon_sections=[axon.hill]+[axon.iseg]+axon.nodes+axon.myelin
        self.soma_sections=[soma.body]
        self.soma_body=soma.body
        self.apical_dendrites=main_apical_dendrite.all_sections+self.seclist(oblique_dends)
        self.somatic_dendrites=self.seclist(somatic_dends)
        self.dendrites=self.apical_dendrites+self.somatic_dendrites
        self.all_sections=self.axon_sections+[self.soma_body]+self.dendrites

        #ensure enough segments are created:

        for sec in self.all_sections:
            sec.nseg=5*geom_nseg(sec,f=200)

class __NeuronRegion(object):
    """
    Base class for axon, soma, dendrite
    """
    #I should establish a connection in regions that the available end of a get_section output is 1
    def connect(self, section,section_end=0,region_end=0): #perhaps also make it able to accept a section? Use Polymorphic concept?
        """
	Gets the segment from the region which it will use to connect,
	the region_end argument is used if the region can be connected
	to from multiple locations (e.g a soma, but unlike an axon.
	
	Each derived class needs a get_connecting_segment accessor
	"""
        
	consegment=self.get_connecting_segment(region_end) #can use argv for region end?
        section.connect(consegment,section_end)

class Soma(__NeuronRegion):

    def __init__ (self,diam=25,length=30,n_soma_seg=1):
        body=h.Section(name='soma')
        body.diam=diam
        body.L=length
        self.body=body
        self.diam=diam
        self.connecting_section='body'

    def get_connecting_segment(self,region_end=0):
        connecting_segment=self.body(region_end)
        return connecting_segment

class DendriticTree(__NeuronRegion):

    def __init__ (self,nseg=5.0,bifurcations=3.0,root_L=100.0,term_L=1.0,
                 root_d=10.0,term_d=1,L_sigma=0.0,branch_prob=1.0): 

        first_section=h.Section()
        first_section.nseg=nseg
        first_section.diam=root_d 
        first_section.L=root_L*grand(L_sigma)
        
        self.all_sections=[]
        self.all_sections.append(first_section)
        self.first_section=first_section

        heads=[self.first_section]                            


        i=0
        while i<bifurcations:
            i+=1
            new_heads=[]
            
            for head in heads:
                if self.__branch_decision(branch_prob): #make decision whether to branch

                    section_length=(term_L-root_L)*i/bifurcations+root_L

                    section_diam=self.__rall_power(head.diam)
                    if section_diam<term_d:
                        section_diam=term_d

                    #make two segments for it:
                    branch1=h.Section()
                    branch1.L=section_length*grand(L_sigma)
                    branch1.diam=section_diam

                    branch2=h.Section()
                    branch2.L=section_length*grand(L_sigma)
                    branch2.diam=section_diam

                    branch1.connect(head,1,0)
                    branch2.connect(head,1,0)

                    new_heads+=[branch1,branch2]
                    
            self.all_sections+=new_heads
            heads=new_heads
	
    def __rall_power(self,parent_diam,e=1.5):
        """
        Returns the diameter of a child section of a branch 
        according to Rall's Power Law as described
        in Van Ooyen et al 2010. Assumes child branches
        will be of equal diameter.
        """

        child_diam=parent_diam/(2**(1/e))
        return child_diam

    def get_connecting_segment(self,region_end=1):
	#connect to the 1-end of the first section of the dendritic tree
        connecting_segment=self.first_section(0)
        return connecting_segment

    def get_connecting_section(self,region_end=1):
	#connect to the 1-end of the first section of the dendritic tree
        connecting_section=self.first_section
        return connecting_section

    def __branch_decision(self,probability):
        """
        For a fixed probability returns a 1 or a 0

        The function is used to decide whether a bifibrication should occur
        """        
        
        import random
        return random.random() < probability

    def distance_scaled_area(self):
        """
        The area is calculated, divided by the distance from the 0 end of the root
        to the 0.5 end of the relative section (linear scaling)
        """

        import math
        num_sections=len(self.all_sections)
        s_asym=0.0

        root=self.all_sections[0]
        rootL=root.L
        roota=section_area(root)

        scaled_area=2.0*roota/rootL

        for i in range(1,num_sections):
            sec=self.all_sections[i]
            seca=section_area(sec)
            rootdistance=abs((fromtodistance(sec(0.5),root(0.0))))
            scaled_area+=seca/rootdistance

        return scaled_area
    
    def bc_asymmetry(self):

        """
        Sum of total area difference between each pair of branched sections
        """
        import math
        num_sections=len(self.all_sections)
        asym=0

        for i in range(1,num_sections/2+1):
            j=i*2
            sec1=self.all_sections[j]
            sec2=self.all_sections[j-1]
            sec1a=section_area(sec1)
            sec2a=section_area(sec2)
            asym+=abs(sec1a-sec2a)

        return asym

    def scaled_bc_asymmetry(self):
        """
        Same as bc_asymmetry but scaled as with distance_scaled_area
        """

        import math
        num_sections=len(self.all_sections)
        s_asym=0.0

        root=self.all_sections[0]

        for i in range(1,num_sections/2+1):
            j=i*2
            sec1=self.all_sections[j]
            sec2=self.all_sections[j-1]
            sec1a=section_area(sec1)
            sec2a=section_area(sec2)

            rootdistance=(fromtodistance(sec1(0.5),root(0.5))+
                         fromtodistance(sec2(0.5),root(0.5)))/2.0
            s_asym+=(abs(sec1a-sec2a)/rootdistance)

        return s_asym

    def children_areas(self):
        """
        Return a dictionary where the keys are sections and the values
        are doubles corresponding to the total area of that section's
        children and its children's children etc.
        """
    
        section_areas={}#Area of the section
        children_areas={}#section with area of its children and their children
        for sec in reversed(self.all_sections):
            sec_area=section_area(sec)
            section_areas[sec]=sec_area

            #if it is a parent itself you need to add its children's area now:
            if sec in children_areas: #if it has associated children areas
                child_area=children_areas[sec]
                extended_area=sec_area+child_area
            else:
                extended_area=sec_area        

            parent=get_parent(sec)

            if parent in children_areas:
                children_areas[parent]+=extended_area
            else:
                children_areas[parent]=extended_area
    
        return children_areas
        
    def bifib1_asymmetry(self):

        """
        Return the total branch-comparitive asymetry measure
        for the branches of the first bifibrication(i.e two branches)
        The children are not taken into account
        """
        import math
        num_sections=len(self.all_sections)
        asym=0

        sec1=self.all_sections[1]
        sec2=self.all_sections[2]
        sec1a=section_area(sec1)
        sec2a=section_area(sec2)
        asym+=abs(sec1a-sec2a)

        return asym

def get_parent(section):

    """
    Return a reference to a section which is a parent of input section
    
    Mainly taken from M.Hines in NEURON+Python forum
    """
    parent = h.SectionRef(sec=section).parent
    return parent

class Axon(__NeuronRegion):
    
    """
    This class returns an axon with an initial segment, hill and number of segment
    depending on what it is passed
    """

    def __init__(self, equiv_diam=20, n_axon_seg=5):
    
        self.myelin = []
        self.nodes = []
        self.iseg = h.Section(name='iseg') #initial segment
        self.connecting_section='hill'
        self.hill = h.Section(name='hill') #Axon Hill
        self.n_axon_seg = n_axon_seg
        
        for count in xrange(n_axon_seg):
            self.myelin.append(h.Section(name='myelin' + str(count)))
            self.nodes.append(h.Section(name='node' + str(count)))
    
        #equiv_diam=math.sqrt(h.area(0.5,sec=h.soma)/(4*math.pi)) #area = equiv_diam^2*4*PI
    
        self.iseg.L = 15   #initial segment between hillock + myelin
        self.iseg.nseg = 5
        for seg in self.iseg:
            seg.diam = equiv_diam / 10.0 #see Sloper and Powell 1982, Fig.71
    
        #taper the hill:
        self.hill.L = 10
        self.hill.nseg = 5
        taper_diam(self.hill, 4 * self.iseg.diam, self.iseg.diam)
    
     
        for i in range(0, n_axon_seg):
            self.myelin[i].nseg = 5 #myelin element
            self.myelin[i].L = 100
            
            for seg in self.myelin[i]:
                seg.diam = self.iseg.diam
    
        for i in range(0, n_axon_seg): #nodes of ranvier
            self.nodes[i].nseg = 1
            self.nodes[i].L = 1.0
            
            for seg in self.nodes[i]:
                seg.diam = self.iseg.diam * 0.75
       
        self.__connect_compartments(n_axon_seg)
              
        
    def __connect_compartments(self, n_axon_seg):
        #self.hill.connect(h.soma,1,0)
        self.iseg.connect(self.hill, 1, 0)
        self.myelin[0].connect(self.iseg, 1, 0)
        self.nodes[0].connect(self.myelin[0], 1, 0)
    
        for i in range(0, n_axon_seg - 1):
            self.myelin[i + 1].connect(self.nodes[i], 1, 0)
            self.nodes[i + 1].connect(self.myelin[i + 1], 1, 0)

    def get_connecting_segment(self,region):
        connecting_segment=self.hill(0)
        return connecting_segment

    def get_connecting_section(self):
        connecting_section=self.hill
        return connecting_section

def fromtodistance(origin_segment, to_segment):
    h.distance(0, origin_segment.x, sec=origin_segment.sec)
    return h.distance(to_segment.x, sec=to_segment.sec)


#Set the mechanism for a section to one value (all segments the same)
def set_section_mechanism(sec, mech, mech_attribute, mech_value): #Is this passing by reference, do you need to state that explicitly in Python?
    for seg in sec:
        setattr(getattr(seg, mech), mech_attribute, mech_value)
        

####################################################
#    method *should* produce the same effect as    #
#    sec.diam(0:1)=zero_bound:one_bound            #
####################################################

#
#    TO DO: Make this into a function as it's much more elegant
#    QUESTION: Methods vs functions, when to use which really?
#    This method needs further testing of its functinality
#
def taper_diam(sec, zero_bound, one_bound):
    dx = 1.0 / (sec.nseg)
    x = dx / 2
    for seg in sec:
        seg.diam = (one_bound - zero_bound) * x + zero_bound
        x += dx
               
#===============================================================================
# NAME: section_area
#
# INPUT: 1 section
#
# OUTPUT: Area of the section as float
#
# REVISION: 1 (14/12/10)
#
# AUTHOR: Mike Vella
#===============================================================================

def section_area(section):
    
    x_list = []
    a = 0
    
    for seg in section:
        x = seg.x
        x_list.append(x)
    
    for x in x_list:
        a += h.area(x, sec=section)
    return a

#===============================================================================
# NOTE: THIS IS STILL INCOMPLETE, need to find a way to figure out the section
# from the segment
#
# NAME: segment_area
#
# INPUT: 1 segment
#
# OUTPUT: Area of the segment as float
#
# REVISION: 1 (14/12/10)
#
# AUTHOR: Mike Vella
#===============================================================================

def segment_area(input_segment):
    
    x = input_segment.x
    a = h.area(x, sec=input_segment.section)
    
    return a



################
#    Spines    #
################

#       Based on the "Folding factor" described in
#       Jack et al (1989), Major et al (1994)
#       note, this assumes active channels are present in spines 
#       at same density as dendrites

def add_spines(dendritic, spine_area, spine_dens):
    
    dendritic_only = h.SectionList()
    
    for sec in dendritic:
        if (sec.name() != 'soma'): #not the nicest way to do this but I'll have to wait till I can find better
            dendritic_only.append(sec)

    for sec in dendritic_only:
        a = section_area(sec)
        F = (sec.L * spine_area * spine_dens + a) / a
        sec.L = sec.L * F ** (2.0 / 3.0)
       
        for seg in sec.allseg():
            seg.diam = seg.diam * F ** (1.0 / 3.0)
            
#===============================================================================
# Routine to load a hoc morphology and do some processing on it
#===============================================================================

def load_3dcell(filename, max_compartment_size=20):

    dendritic = h.SectionList()

    for sec in h.allsec():
        del sec #is this correct?
      
    h.xopen(filename)
    h('access soma')
    
    #make sure no compartments exceed 50 uM length
    for sec in h.allsec():
        diam_save = sec.diam #sec.diam makes no sense does it since diam is a segment property
        n = sec.L / max_compartment_size 
        n_truncated = int(n)#use a truncating division to avoid error
        sec.nseg = n_truncated + 1 
        if h.n3d() == 0:
            sec.diam = diam_save
        dendritic.append()
        
    return dendritic

#===============================================================================
# NAME: remove_soma 
#
# INPUT: 1 sectionlist
#
# OUTPUT: 1 sectionlist not containing the section with the name 'soma'
#
# REVISION: 1 (14/12/10)
#
# AUTHOR: Mike Vella
#===============================================================================

def remove_soma(input_sectionlist):
    return_sectionlist = h.SectionList()
    
    for sec in input_sectionlist:
        if sec.name() != 'soma':
            return_sectionlist.append()
    
    return return_sectionlist

#===============================================================================
# NAME: print_report
#
# INPUT: n/a
#
# OUTPUT: Prints a psection() of each section and the topology
#
# REVISION: 1 (14/12/10)
#
# AUTHOR: Mike Vella
#===============================================================================

def print_report():
    
    for sec in h.allsec():
        print h.psection()
    print h.topology()
