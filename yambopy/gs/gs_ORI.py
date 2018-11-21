# Copyright (C) 2015 Henrique Pereira Coutada Miranda
# All rights reserved.
#
# This file is part of yambopy
#
#from __future__ import print_function
from qepy import *
#from schedulerpy import *
#import argparse
from yambopy import *
#from yambopy.plot  import *
import os

#parser = argparse.ArgumentParser(description='Convergence test of the colomb cutoff')
#parser.add_argument('-r' ,'--relax',      action="store_true", help='relaxation')
#parser.add_argument('-s' ,'--scf',        action="store_true", help='scf')
#parser.add_argument('-n' ,'--nscf',       action="store_true", help='nscf')
#parser.add_argument('-b' ,'--bands',      action="store_true", help='bands')
#args = parser.parse_args()
#
#class GSrunner():
#
# # Number of cores for calculation
# cores=8
#  
# # Normal Band Structure
# p = Path([ [[0.0,0.0,0.0],'G'],
#            [[0.5,0.0,0.0],'M'],
#            [[0.3333,0.3333,0.0],'K'],
#            [[0.0,0.0,0.0],'G']], [80,80,80])
# #
# # Create the input files
# #
def get_inputfile():
    """ Define a Quantum espresso input file for MoS2 
    """
    qe = PwIn()
    qe.atoms = [['Mo',[0.333333333 , 0.666666667 ,  0.000000000 ]],
                ['S' ,[0.666666667 , 0.333333333 ,  0.072751696 ]],
                ['S' ,[0.666666667 , 0.333333333 , -0.072751696 ]]]
    qe.atypes = {'Mo': [95.940,"Mo_RL_withPS_PZ.UPF"], 'S' : [32.065,"S.rel-pz-n-nc.UPF"]}

    qe.control['prefix']          = "'mos2'"
    qe.control['wf_collect']      = '.true.'
    qe.system['force_symmorphic'] = ".true."
    qe.system['celldm(1)']        = 5.96 
    qe.system['celldm(3)']        = 40.0/qe.system['celldm(1)'] 
    qe.system['ecutwfc']          = 100 
    qe.system['occupations']      = "'fixed'"
    qe.system['nat']              = 3
    qe.system['ntyp']             = 2
    qe.system['ibrav']            = 4
    qe.system['lspinorb']         = '.true.'
    qe.system['noncolin']         = '.true.'
    qe.electrons['conv_thr']      = 1e-10
    qe.kpoints                    = [18, 18, 1]
    return qe
#relax
def relax():
    os.system('mkdir -p relax') 
    qe = get_inputfile()
    qe.control['calculation'] = "'relax'"
    qe.ions['ion_dynamics']   = "'bfgs'"
    qe.cell['cell_dynamics']  = "'bfgs'"
    qe.cell['cell_dofree']    = "'2Dxy'"
    print("running relax:")
    kpoints = [[12,12,1]] 
    for line in kpoints:
    #for line in ecut:
      qe.kpoints = line
      qe.system['ecutwfc'] = 80 
      name    = 'kpoint-' + str(line[0]) + '.scf'
      nameout = 'kpoint-' + str(line[0]) + '.out'
      qe.control['prefix'] = "\'%s\'" %  ('ecut-' + str(line[0]))
      qe.write('relax/'+name)
#      job = pbs(nodes=1,core=cores,dependent=0,queue="batch",name='qe-relax',walltime="2:00:00")
#      job.add_command('module load espresso/5.4.0')
#      job.add_command('export ESPRESSO_PSEUDO=\'/home/alexandre/home2/pseudos\'')
#      job.add_command('cd relax')
#      job.add_command('mpirun -np %d pw.x -inp %s | tee %s'%(cores,name,nameout))
#      job.write("relax.sh")
#      job.run()

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

#nscf
def nscf():
    folder_nscf='nscf-51x51'
    if not os.path.isdir(folder_nscf):
        os.mkdir(folder_nscf)
    qe = get_inputfile()
    qe.control['calculation']      = "'nscf'"
    qe.electrons['diago_full_acc'] = ".true."
    qe.electrons['conv_thr']       = 1e-09
    qe.system['nbnd']              = 74 
    qe.kpoints = [51, 51, 1]
    qe.write('%s/mos2.nscf'%folder_nscf)
    yambo = pbs(nodes=1,core=cores,dependent=0,queue="batch",name='qe-nscf',walltime="12:00:00")
    yambo.add_command('module load espresso/5.4.0')
    yambo.add_command('export ESPRESSO_PSEUDO=\'/home/alexandre/home2/pseudos\'')
    yambo.add_command('cp -r ./scf/mos2.save %s/' % folder_nscf)
    yambo.add_command('cd %s'%folder_nscf)
    yambo.add_command('mpirun -np %d pw.x -nk %s -inp mos2.nscf | tee nscf.out'%(cores,cores))
    yambo.run()
#bands
def bands():
    folder_bands='bands'
    if not os.path.isdir(folder_bands):
      os.mkdir('bands')
    qe = get_inputfile()
    qe.control['calculation'] = "'bands'"
    qe.electrons['diago_full_acc'] = ".true."
    qe.electrons['conv_thr'] = 1e-8
    qe.system['nbnd'] = 40 
    qe.system['force_symmorphic'] = ".true."
    qe.ktype = 'crystal'
    qe.set_path(p)
    qe.write('bands/mos2.bands')
#    yambo = pbs(nodes=1,core=cores,dependent=0,queue="batch",name='qe-bands',walltime="2:00:00")
#    yambo.add_command('module load espresso/5.4.0')
#    yambo.add_command('export ESPRESSO_PSEUDO=\'/work/projects/tss-physics/pseudos/espresso\'')
#    yambo.add_command('cp -r scf/mos2.save %s/' % folder_bands)
#    yambo.add_command('cd %s' % folder_bands)
#    yambo.add_command('mpirun -np %d pw.x -inp mos2.bands | tee bands.out'%(cores))
#    yambo.run()
