#
#       Copyright (C) 2018-2019 the YAMBOpy team
#      https://github.com/henriquemiranda/yambopy
#
# Authors (see AUTHORS file for details): HM
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
 This is an example of a BSE calculation for MoS2 
 using the new Flow/Task methods of yambopy.
 The approach is the same as the one implemented in Abipy.
"""
from yambopy.data.structures import MoS2
from qepy.pw import PwIn
from yambopy.flow import YambopyFlow, PwTask, P2yTask, YamboTask

#create a QE scf task and run
qe_input = PwIn.from_structure_dict(MoS2,kpoints=[12,12,1],ecut=30)
qe_scf_task = PwTask.from_input(qe_input)

#create a QE nscf task and run
qe_input = qe_input.copy().set_nscf(20)
qe_nscf_task = PwTask.from_input([qe_input,qe_scf_task],dependencies=qe_scf_task)

#create a p2y nscf task and run
p2y_task = P2yTask.from_nscf_task(qe_nscf_task)

#create a yambo optics task and run
yamboin_dict = dict(NGsBlkXs=[1,'Ry'],
                    BndsRnXs=[[1,20],''],
                    BSEBands=[[8,11],''],
                    BEnRange=[[0.0,6.0],'eV'],
                    BEnSteps=[1000,''])

yambo_task = YamboTask.from_runlevel(p2y_task,'-b -o b -k sex -y d',
                                     yamboin_dict,dependencies=p2y_task)
print(yambo_task)

#create yamboflow
yambo_flow = YambopyFlow.from_tasks('flow',[qe_scf_task,qe_nscf_task,p2y_task,yambo_task])
print(yambo_flow)
yambo_flow.create()
yambo_flow.dump_run()
print(yambo_flow)
yambo_flow.run()
