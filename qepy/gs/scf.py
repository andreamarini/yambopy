#
#       Copyright (C) 2018-2019 the YAMBOpy team
#      https://github.com/henriquemiranda/yambopy
#
# Authors (see AUTHORS file for details): AM
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
from qepy import pw
from qepy.data.structures import Materials
import os

#scf
def scf(material):
    """
    SCF loop
    """
    scf_folder='scf'
    if not os.path.isdir('%s'%scf_folder):
        os.mkdir('%s'%scf_folder)
    qe=pw.PwIn
    qe=pw.PwIn.from_structure_dict(Materials[material])
#,kpoints=[12,12,1])
    qe.control['calculation']     = "'scf'"
    qe.system['force_symmorphic'] = ".true."
    qe.write('{}/{}.scf'.format(scf_folder,material))
#
#    yambo = pbs(core=cores,dependent=0,queue="batch",name='qe-scf',walltime="3:00:00")
#    yambo.add_command('module load espresso/5.4.0')
#    yambo.add_command('export ESPRESSO_PSEUDO=\'/home/alexandre/home2/pseudos\'')
#    yambo.add_command('cd %s'%scf_folder)
#    yambo.add_command('mpirun -np %d pw.x -inp mos2.scf | tee scf.out'%(cores))
#    yambo.run()
