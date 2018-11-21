# Copyright (C) 2015 Henrique Pereira Coutada Miranda
# All rights reserved.
#
# This file is part of yambopy
#
from qepy import *
from yambopy import *
import os

#scf
def scf():
    """
    SCF loop
    """
    scf_folder='scf'
    if not os.path.isdir('%s'%scf_folder):
        os.mkdir('%s'%scf_folder)
    qe = get_inputfile()
    qe.control['calculation']     = "'scf'"
    qe.write('%s/mos2.scf'%scf_folder)
#    yambo = pbs(core=cores,dependent=0,queue="batch",name='qe-scf',walltime="3:00:00")
#    yambo.add_command('module load espresso/5.4.0')
#    yambo.add_command('export ESPRESSO_PSEUDO=\'/home/alexandre/home2/pseudos\'')
#    yambo.add_command('cd %s'%scf_folder)
#    yambo.add_command('mpirun -np %d pw.x -inp mos2.scf | tee scf.out'%(cores))
#    yambo.run()

