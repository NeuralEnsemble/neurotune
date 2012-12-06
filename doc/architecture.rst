Optimal Neuron Architecture
===========================

Optimal Neuron provides three main classes: Optimizers, Evaluators
and Controllers.

Optimizer Class
---------------
The optimizer decides the mating,survival and death of individuals (each
individaul being a simulation).
The optimizer does this by starting with
an initial population chosen randomly (Say we had a population of 100,
with 3 free paramaters x,y,z, the population is therefore 100 members
[x1,y1,z1]. . . [x100,y100,z100] in order to evaluate this population, the op-
timizer passes every member to the evaluator which assigns each indivudal
a tness based on the simulation output.

Evaluator Class
---------------
But how does the Evaluator do this?
The evaluator does the above by
looking at simulation output and targets and assigning a tness (via its
cost function). The evaluator needs a way to run each simulation - this is
why it needs a controller.
Hence there are things like IClampEvalutor -
This evaluator specically evaluates the tness of a current clamp simulation
compared to the exeperimental data. - It passes those tness results back to
the optimizer, the optimizer doesn't need to know what kind of simulation
is being run to obtain these tnesses.

Controller Class
---------------
The controller class implements the actual running of the simulation given
the parameters. A controller will provide the evaluator with a run() method
and hide the details of the simulation implementation from the evaluator.


Why this architecture?
---------------------
This architecture decouples the optimization from the actual assigining of
tness and the actual control of a simulation.
The ability easily mix and
match optimizers, controllers and evaluators gives great exibility. For in-
stance, the CLI Controller used in the musclemodel doesn't need to be a
Python script- it just needs to be a program which can accept a command
line argument and run a simulation based on it.

What is a dumb evaluator?
-------------------------
Most evaluators work by receiving a trace back from the simulation and
assessing its tness. A dumb evalutor is a bit special - The simulation itself
reports a tness and writes it to a le. The evaluator is dumb because all it
needs to do is read this tness value and report that back to the Optimizer.
This allows a lot of exibility (If a user nds that the given evaluators don't
match their needs but doesn't want the hassle of writing their own evaluator
(e.g doesn't feel comfortable with OOP) they don't have to).
2
