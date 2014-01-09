# WARNING: This example may not yet be working.  Please check again in
#          the upcoming release.
#
# This is an example to demonstrate how the output of abstracting a switched
# system, where the only control over the dynamics is through mode switching
# might look like.

# NO, 6 Jan 2014.

# We will assume, we have the 6 cell robot example.

#
#     +---+---+
#     | 2 | 3 |
#     +---+---+
#     | 0 | 1 | 
#     +---+---+
#

from tulip import spec, synth, transys
import numpy as np
from scipy import sparse as sp


###############################
# Switched system with 2 modes:
###############################

# In this scenario we have limited actions "left, right" with 
# uncertain (nondeterministics) outcomes (e.g., due to bad actuators or 
# bad low-level feedback controllers)

# Only control over the dynamics is through mode switching
# Transitions should be interpreted as nondeterministic

# Create a finite transition system
env_sws = transys.OpenFTS()

env_sws.sys_actions.add_from({'right','left'})

# str states
n = 4
states = transys.prepend_with(range(n), 's')
env_sws.states.add_from(set(states) )

# mode1 transitions
transmat1 = np.array([[0,1,0,1],
                      [0,1,0,0],
                      [0,1,0,1],
                      [0,0,0,1]])
env_sws.transitions.add_labeled_adj(
    sp.lil_matrix(transmat1), states, {'sys_actions':'right'}
)
                      
# mode2 transitions
transmat2 = np.array([[1,0,0,0],
                      [1,0,1,0],
                      [0,0,1,0],
                      [1,0,1,0]])
env_sws.transitions.add_labeled_adj(
    sp.lil_matrix(transmat2), states, {'sys_actions':'left'}
)


# Decorate TS with state labels (aka atomic propositions)
env_sws.atomic_propositions.add_from(['home','lot'])
env_sws.states.labels(
    states, [set(),set(),{'home'},{'lot'}]
)

# This is what is visible to the outside world (and will go into synthesis method)
print(env_sws)

#
# Environment variables and specification
#
# The environment can issue a park signal that the robot just respond
# to by moving to the left of the grid.  We assume that
# the park signal is turned off infinitely often.
#
env_vars = {'park'}
env_init = {'eloc = 0', 'park'}
env_prog = {'!park'}
env_safe = set()                # empty set

# 
# System specification
#
# The system specification is that the robot should repeatedly revisit
# the right side of the grid while at the same time responding
# to the park signal by visiting the left side.  The LTL
# specification is given by 
#
#     []<> home && [](park -> <>lot)
#
# Since this specification is not in GR(1) form, we introduce the
# variable X0reach that is initialized to True and the specification
# [](park -> <>lot) becomes
#
#     [](next(X0reach) <-> lot || (X0reach && !park))
#

# Augment the environmental description to make it GR(1)
#! TODO: create a function to convert this type of spec automatically

# Define the specification
#! NOTE: maybe "synthesize" should infer the atomic proposition from the 
# transition system? Or, we can declare the mode variable, and the values
# of the mode variable are read from the transition system.
sys_vars = {'X0reach'}
sys_init = {'X0reach'}          
sys_prog = {'home'}               # []<>home
sys_safe = {'next(X0reach) <-> lot || (X0reach && !park)'}
sys_prog |= {'X0reach'}

# Create the specification
specs = spec.GRSpec(env_vars, sys_vars, env_init, sys_init,
                    env_safe, sys_safe, env_prog, sys_prog)
                    
# Controller synthesis
#
# At this point we can synthesize the controller using one of the available
# methods.  Here we make use of JTLV.
#
ctrl = synth.synthesize('gr1c', specs, env=env_sws, ignore_env_init=True)

# Generate a graphical representation of the controller for viewing
if not ctrl.save('robot_controlled_switching.png', 'png'):
    print(ctrl)
