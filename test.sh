set -e

#### Requires NEURON
cd examples/example_1
nrnivmodl
python optimization.py -nogui         # run one of the examples supressing plots etc.

#### Requires NEURON
cd ../../examples/example_2
nrnivmodl
python optimization.py -nogui         # run one of the examples supressing plots etc.

cd ../../examples/example_3
python SineWaveOptimizer.py -nogui  # run one of the examples supressing plots etc.

cd ../../examples/example_4
python SineWavePointOptimizer.py -nogui  # run one of the examples supressing plots etc.

cd ../../examples/example_5
python SineWaveNetworkOptimizer.py -nogui
