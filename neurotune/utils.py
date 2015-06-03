'''

    Script to plot evolution of parameters in neurotune
    
'''
        
import math

def plot_generation_evolution(sim_var_names, target_values = {}):
    
    import matplotlib.pyplot as pylab

    individuals_file_name = '../data/ga_individuals.csv'

    individuals_file = open(individuals_file_name)

    generations = []
    generations_all = []
    generations_offset = []

    f = []
    nrows = 3
    val_num = len(sim_var_names)
    ncols = math.ceil(val_num/3.0)
    population_total = 0
    generations_total = 0
    
    for line in individuals_file:
        generation = int(line.split(',')[0])
        if generation==0:
            population_total+=1
        generations_total = generation

    vals = {}
    colours = {}
    sizes = {}

    for i in range(val_num):
        vals[i]=[]
        colours[i]=[]
        sizes[i]=[]
        
    individuals_file = open(individuals_file_name)
    

    for line in individuals_file:
        main_info = line.split('[')[0]
        values = line.split('[')[1]
        generation = int(main_info.split(',')[0])
        individual = int(main_info.split(',')[1].strip())
        fitness = float(main_info.split(',')[2].strip())

        if individual == 0:
            generations.append(generation)
        generations_all.append(generation)
        generations_offset.append(generation+(individual/40.0))
        f.append(fitness)

        val_strings = values[:-2].split(',')

        for i in range(len(val_strings)):
            vals[i].append(float(val_strings[i].strip()))
            colours[i].append(individual)
            sizes[i].append((population_total-individual)*2)
            
    fig = pylab.figure()
    fig.canvas.set_window_title("Evolution over %i generations of %s"%(generations_total, sim_var_names))

    for i in range(val_num):

        pylab.subplot(nrows, ncols, i)
        pylab.title(sim_var_names[i])
        if target_values is not None and target_values.has_key(sim_var_names[i]):
            value = target_values[sim_var_names[i]]
            x = [-1,generations_total+1]
            y = [value,value]
            pylab.plot(x,y,'--', color='grey')
            
        pylab.scatter(generations_offset, vals[i], s=sizes[i], c=colours[i], alpha=0.4)
        if i==0:
            pylab.xlabel("Generation (%i individuals, offset slightly; larger circle => fitter)"%(population_total))


    fig = pylab.figure()
    
    fig.canvas.set_window_title("Fitness over %i generations from %s"%(generations_total, individuals_file_name))
    ax = fig.add_subplot(2,1,1)

    ax.scatter(generations_offset, f, s=sizes[i], c=colours[i], alpha=0.4)
    ax = fig.add_subplot(2,1,2)
    ax.set_yscale('log')
    ax.scatter(generations_offset, f, s=sizes[i], c=colours[i], alpha=0.4)
    pylab.xlabel("Generation (%i individuals, offset slightly; larger circle => fitter)"%(population_total))

    pylab.show()

if __name__ == '__main__':
    
    # example 3
    target_values = {'amp':     65,
                    'period':  250,
                    'offset':  -10}
                    
    # example 2
    target_values = {'axon_gbar_na': 3661.79,
           'axon_gbar_kv': 23.23,
           'axon_gbar_kv3': 0.26,
           'soma_gbar_na': 79.91,
           'soma_gbar_kv': 0.58,
           'soma_gbar_kv3': 1.57}
           
    parameters = ['leak_cond_density',
                  'k_slow_cond_density',
	              'k_fast_cond_density',
                  'ca_boyle_cond_density', 
                  'specific_capacitance',
                  'leak_erev',
                  'k_slow_erev',
                  'k_fast_erev',
                  'ca_boyle_erev']
    
    #plot_generation_evolution(target_values.keys(), target_values)
    plot_generation_evolution(parameters)