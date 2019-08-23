#
#       Copyright (C) 2018-2019 the YAMBOpy team
#      https://github.com/henriquemiranda/yambopy
#
# Authors (see AUTHORS file for details): HM AM
# 
# This file is distributed under the terms of the GNU 
# General Public License. You can redistribute it and/or 
# modify it under the terms of the GNU General Public 
# License as published by the Free Software Foundation; 
# either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will 
# be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A 
# PARTICULAR PURPOSE.  See the GNU General Public License 
# for more details.
#
# You should have received a copy of the GNU General Public 
# License along with this program; if not, write to the Free 
# Software Foundation, Inc., 59 Temple Place - Suite 330,Boston, 
# MA 02111-1307, USA or visit http://www.gnu.org/copyleft/gpl.txt.
#

"""
This file contains examples of structures

https://www.python-course.eu/dictionaries.php

passed to pw.py can be used with

from_structure_dict
  | def set_structure(self,structure):
  |  |def set_lattice(self,ibrav=None,celldm1=None,celldm2=None,celldm3=None,
  |  |def set_atoms(self,atoms,coordtype="reduced"):
  |  |def set_atypes(self,atypes):
  |
  | def set_kpoints(self,kpoints,shiftk=[0,0,0]):
  | def set_ecut(self,ecut):
  | def set_spinorbit(self):

    def set_nscf(self,nbnd,nscf_kpoints=None,conv_thr=1e-8,
    def set_relax(self,cell_dofree=None):
    def set_path(self,path):
    def set_atoms_string(self,string):
    def set_atoms_ase(self,atoms):


"""

__all__ = [
    "Materials",
]
#
Materials = { "BN":[], "MoS2":[], "Si":[]}
#
#BN
lattice = dict(ibrav=4,celldm1=4.7,celldm3=12)
atypes = dict(B=[10.811, "B.pbe-mt_fhi.UPF"],
              N=[14.0067,"N.pbe-mt_fhi.UPF"])
atoms = [['N',[ 0.0, 0.0,0.5]],
         ['B',[1./3,2./3,0.5]]]
Materials["BN"]= dict(lattice=lattice,atypes=atypes,atoms=atoms,prefix="'BN'") 
#
#MoS2
a = 5.838
c = 18
#    qe.system['celldm(1)']        = 5.96 
#    qe.system['celldm(3)']        = 40.0/qe.system['celldm(1)'] 
lattice = dict(ibrav=4,celldm1=5.838,celldm3=c/a) 
#    qe.atypes = {'Mo': [95.940,"Mo_RL_withPS_PZ.UPF"], 'S' : [32.065,"S.rel-pz-n-nc.UPF"]}
atypes = dict(Mo=[95.94, "Mo.pz-mt_fhi.UPF"],
              S =[32.065, "S.pz-mt_fhi.UPF"]) 
atoms = [['Mo',[2./3,1./3,          0.0]],
         [ 'S',[1./3,2./3, 2.92781466/c]],
         [ 'S',[1./3,2./3,-2.92781466/c]]]
Materials["MoS2"]= dict(lattice=lattice,atypes=atypes,atoms=atoms,prefix="'MoS2'")
Materials["MoS2"]["soc"]="true"
Materials["MoS2"]["ecut"]=100
#    qe._atoms = [['Mo',[0.333333333 , 0.666666667 ,  0.000000000 ]],
#                 ['S' ,[0.666666667 , 0.333333333 ,  0.072751696 ]],
#                 ['S' ,[0.666666667 , 0.333333333 , -0.072751696 ]]]
#    qe.control['wf_collect']      = '.true.'
#    qe.system['occupations']      = "'fixed'"
#    qe.electrons['conv_thr']      = 1e-10
#    qe.kpoints                    = [18, 18, 1]
#
#Si
lattice = dict(ibrav=2,celldm1=10.3)
atypes = dict(Si=[28.086,"Si.pbe-mt_fhi.UPF"])
atoms = [['Si',[0.125,0.125,0.125]],
         ['Si',[-.125,-.125,-.125]]]
Materials["Si"]= dict(lattice=lattice,atypes=atypes,atoms=atoms,prefix="'Si'") 

