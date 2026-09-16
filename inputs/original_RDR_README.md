# SolProp for Thermodynamics-informed Graph Neural Networks for Phase Transition Enthalpies

Here the data and static code of the work "Thermodynamics-informed Graph Neural Networks for Phase Transition Enthalpies" is published. The code here specifically includes the physics informed loss functions.
The code for the SolProp library: https://gitlab.kuleuven.be/creas/vermeiregroup/solprop.

## Requirements and installation
SolProp has been so far tested to work on Mac and Linux OS. It may not work on Windows.
The package requirements are listed in the 'requirements.txt' file.

## Supported molecules
SolProp currently supports prediction for only electrically neutral compounds containing H, B, C, N, O, S, P,
F, Cl, Br, and I and nonionic liquid molecules. Predictions for any out-of-range solvents and solutes won't be reliable.

## Definitions of inputs and outputs
The definitions of prediction inputs and outputs are described in the 'inp.py' file.

### Data reading
The solute/solvent smiles or inchis are read from (1) a csv file, or (2) a pandas dataframe. The columns names for the prediction and training can be set in the 'inp.py' file.

## License Information
SolProp is a free, open-source software package distributed under the MIT license.

## Data
A digitized version of the Phase transition enthalpy compendium from Acree, W. and Chickos, J. S. is added. 

Please cite the following sources if you use it in your work: 
[1] Acree, W. and Chickos, J. S. Phase Transition Enthalpy Measurements of Organic and Organometallic Compounds. Sublimation, Vaporization and Fusion Enthalpies From 1880 to 2015. Part 1. C1-C10. Journal of Physical and Chemical Reference Data 2016, 45 
[2] Acree, W. and Chickos, J. S. Phase Transition Enthalpy Measurements of Organic and Organometallic Compounds and ionic liquids. Sublimation, Vaporization, and Fusion Enthalpies From 1880 to 2015. part 2. C11-C192. Journal of Physical and Chemical Reference Data 2017, 46 
[3] Acree, W. and Chickos, J. S. Phase Transition Enthalpy Measurements of Organic Compounds. An Update of Sublimation, Vaporization, and Fusion Enthalpies from 2016 to 2021. Journal of Physical and Chemical Reference Data 2022, 51
