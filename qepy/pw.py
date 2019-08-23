#
#       Copyright (C) 2018-2019 the YAMBOpy team
#      https://github.com/henriquemiranda/yambopy
#
# Authors (see AUTHORS file for details): HM AMS
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
import os
import re
import shutil
from math import sqrt
from qepy import qepyenv
from .pseudo import get_pseudo_path
from .tools import fortran_bool
from .lattice import red_car, car_red

class PwIn(object):
    """
    Class to generate an manipulate Quantum Espresso input files
    Can be initialized either reading from a file or starting from a new file.
    This class is not meant to be comprehensive but a lightweight version 
    capable of basic input/ouput of PW files.
    For a comprehensive class use the tools provoded by the AiiDa package: http://www.aiida.net/

    Examples of use:

    To read a local file with name "mos2.in"

        .. code-block :: python

            qe = PwIn.from_file('mos2.scf')
            print qe

    To start a file from scratch

        .. code-block :: python

            qe = PwIn()
            qe._atoms = [['N',[ 0.0, 0.0,0.0]],
                        ['B',[1./3,2./3,0.0]]]
            qe.atypes = {'B': [10.811, "B.pbe-mt_fhi.UPF"],
                         'N': [14.0067,"N.pbe-mt_fhi.UPF"]}

            qe.control['prefix'] = "'%s'"%prefix
            qe.control['verbosity'] = "'high'"
            qe.control['wf_collect'] = '.true.'
            qe.control['pseudo_dir'] = "'../pseudos/'"
            qe.system['celldm(1)'] = 4.7
            qe.system['celldm(3)'] = layer_separation/qe.system['celldm(1)']
            qe.system['ecutwfc'] = 60
            qe.system['occupations'] = "'fixed'"
            qe.system['nat'] = 2
            qe.system['ntyp'] = 2
            qe.system['ibrav'] = 4
            qe.kpoints = [6, 6, 1]
            qe.electrons['conv_thr'] = 1e-8

            print qe

    Special care should be taken with string variables e.g. "'high'"

    """
    _pw = 'pw.x'

    def __init__(self):
        """ TODO: specify the required parameters """
        #atoms
        self._atoms = []
        #kpoints
        self.ktype = "automatic"
        self.kpoints = [1,1,1]
        self.shiftk = [0,0,0]
        self.klist = []
        #dictionaries
        self.control = dict(prefix="'pw'",wf_collect='.true.',verbosity="'high'")
        self.system = dict()
        self.electrons = dict(conv_thr=qepyenv.CONV_THR)
        self.ions = dict()
        self.cell = dict()
        self.atypes = dict()
        self.cell_units = 'bohr'
        self.atomic_pos_type = 'crystal'

    @classmethod
    def from_file(cls,filename):
        """ Initialize the QE structure from a file """
        new = cls()
 
        with open(filename,"r") as f:
            new.file_lines = f.readlines() #set file lines
            new.store(new.control,"control")     #read &control
            new.store(new.system,"system")      #read &system
            new.store(new.electrons,"electrons")   #read &electrons
            new.store(new.ions,"ions")        #read &ions
            new.store(new.cell,"cell")        #read &ions
            #read ATOMIC_SPECIES
            new.read_atomicspecies()
            #read ATOMIC_POSITIONS
            new.read_atoms()
            #read K_POINTS
            new.read_kpoints()
            #read CELL_PARAMETERS
            new.read_cell_parameters()

        return new

    @classmethod
    def from_structure_dict(cls,structure,kpoints=None,pseudo_dir='.',conv_thr=None):
        pwi = cls()
        pwi.set_structure(structure)
        pwi.control['prefix'] = structure['prefix']
        if kpoints: pwi.set_kpoints(kpoints)
        if structure["ecut"]: 
         pwi.set_ecut(structure["ecut"])
        if pseudo_dir: pwi.pseudo_dir = pseudo_dir
        if conv_thr: pwi.electrons['conv_thr'] = conv_thr
        if structure["soc"]: 
         pwi.set_spinorbit()
        return pwi
      
    @property
    def natoms(self): 
        return len(self._atoms)

    @property
    def pseudo_dir(self):
        if 'pseudo_dir' not in self.control: return None
        return self.control['pseudo_dir'].replace("'",'')
    
    @pseudo_dir.setter
    def pseudo_dir(self,value):
        self.control['pseudo_dir'] = "'%s'"%value.replace("'",'')

    @property
    def prefix(self): 
        return self.control['prefix'].replace("'",'')

    @prefix.setter
    def prefix(self,value):
        self.control['prefix'] = "'%s'"%value.replace("'",'')

    def set_ecut(self,ecut):
        self.system['ecutwfc'] = ecut

    def set_structure(self,structure):
        """
        Set the structure from a structure dictionary
        
        Example:
            .. code-block :: python
            
            structure = dict(ibrav=4,celldm1=4.7,celldm3=12)
            atypes = dict(Si=[28.086,"Si.pbe-mt_fhi.UPF"])
            atoms = [['N',[ 0.0, 0.0,0.5]],
                     ['B',[1./3,2./3,0.5]]]
            BN = dict(structure=structure,atypes=atypes,atoms=atoms)

            pwi = PwIn()
            pwi.set_structure(BN)
        """
        if 'lattice' in structure: self.set_lattice(**structure['lattice'])
        if 'atypes'  in structure: self.set_atypes(structure['atypes'])
        if 'atoms'   in structure: self.set_atoms(structure['atoms'])

    def get_structure(self):
        """ Return an instance of a structure dictionary
        """
        lattice = self.get_lattice()
        return dict(lattice=lattice,atypes=self.atypes,atoms=self._atoms)

    def change_cell_parameters(self):
        """
        Convert the atomic postions to cartesian, change the lattice and convert
        the atomic positions to reduced
        """
        raise NotImplementedError('TODO')

    def set_lattice(self,ibrav=None,celldm1=None,celldm2=None,celldm3=None,
                      celldm4=None,celldm5=None,celldm6=None,cell_parameters=None):
        """Set the structure using the typical QE input variables"""
        if ibrav == 0 and cell_parameters is None:
            raise ValueError('ibrav = 0 implies that the cell_parameters variable is set')
        if cell_parameters: self.cell_parameters = cell_parameters
        if ibrav is not None: self.ibrav = ibrav
        if celldm1 is not None: self.system['celldm(1)'] = celldm1
        if celldm2 is not None: self.system['celldm(2)'] = celldm2
        if celldm3 is not None: self.system['celldm(3)'] = celldm3
        if celldm4 is not None: self.system['celldm(4)'] = celldm4
        if celldm5 is not None: self.system['celldm(5)'] = celldm5
        if celldm6 is not None: self.system['celldm(6)'] = celldm6

    def get_lattice(self):
        lattice_dict = {}
        if 'ibrav' in self.system: lattice_dict['ibrav'] = self.ibrav 
        if 'celldm(1)' in self.system: lattice_dict['celldm1'] = self.system['celldm(1)']
        if 'celldm(2)' in self.system: lattice_dict['celldm2'] = self.system['celldm(2)']
        if 'celldm(3)' in self.system: lattice_dict['celldm3'] = self.system['celldm(3)']
        if 'celldm(4)' in self.system: lattice_dict['celldm4'] = self.system['celldm(4)']
        if 'celldm(5)' in self.system: lattice_dict['celldm5'] = self.system['celldm(5)']
        if 'celldm(6)' in self.system: lattice_dict['celldm6'] = self.system['celldm(6)']
        if self.ibrav == 0: lattice_dict['cell_parameters'] = self.cell_parameters
        return lattice_dict 

    def set_atoms(self,atoms,coordtype="reduced"):
        """
        Set the atoms.
        Internally the atoms are always stored in reduced coordinates.
        The positions are written/read in the format from atomic_pos_type

        Arguments:
            coordtype: ("reduced"/"crystal") or cartesian

        Example:
            .. code-block :: python
   
                pwi = PwIn()
                pwi.set_atoms( [['Si',[0.125,0.125,0.125]],
                                ['Si',[-.125,-.125,-.125]]])
        """
        self.system['nat'] = len(atoms)
        #TODO: add consistency check 

        #convert the positions if needed
        if coordtype in ["reduced","crystal"]:
            self._atoms = atoms
        else:
            red_atoms = []
            for atype,apos in atoms:
                red_atoms.append( [atype,car_red([apos],self.cell_parameters)[0]] )
            self._atoms = red_atoms 

    def set_atypes(self,atypes):
        """"
        Set the atom types.

        Example:
            .. code-block :: python
                pwi = PwIn()
                pwi.set_atypes({'Si': [28.086,"Si.pbe-mt_fhi.UPF"]})
        """
        self.system['ntyp'] = len(atypes)
        #TODO: add consistency check
        self.atypes = atypes

    def set_nscf(self,nbnd,nscf_kpoints=None,conv_thr=1e-8,
                 diago_full_acc=True,force_symmorphic=True):
        """
        set the calculation to be nscf
        """
        self.control['calculation'] = "'nscf'"
        self.electrons['conv_thr'] = conv_thr
        self.system['nbnd'] = nbnd
        self.electrons['diago_full_acc'] = fortran_bool(diago_full_acc)
        self.system['force_symmorphic'] = fortran_bool(force_symmorphic)
        if nscf_kpoints: self.set_kpoints(nscf_kpoints) 
        return self

    def set_relax(self,cell_dofree=None):
        """
        set the calculation to be relax
        """
        self.control['calculation'] = "'relax'"
        self.ions['ion_dynamics']  = "'bfgs'"
        if cell_dofree: 
            self.control['calculation'] = "'vc-relax'"
            self.cell['cell_dynamics']  = "'bfgs'"
            self.cell['cell_dofree'] = "'%s'"%cell_dofree

    def set_spinorbit(self):
        self.system['lspinorb'] = '.true.'
        self.system['noncolin'] = '.true.'

    def get_pseudos(self,destpath='.',pseudo_paths=[],verbose=0):
        """
        Check if the pseudopotential files can be found in the specified path
        and copy them to destpath
        """
        import qepy.data.pseudos as qe_pseudos
        pseudo_paths.append(os.path.dirname(qe_pseudos.__file__))

        #use pseudo_dir from control
        if self.pseudo_dir:
            if os.path.isdir(self.pseudo_dir): 
                pseudo_paths.append(self.pseudo_dir)
       
        ppstring = '\n'.join(pseudo_paths)
        if verbose: print('List of pseudo_paths:\n'+ppstring)

        #find all the pseudopotentials
        for atype,(mass,pseudo_filename) in self.atypes.items():
            pseudo_filename = get_pseudo_path( pseudo_filename, pseudo_paths )
            if pseudo_filename is None:
                err_msg = 'Pseudopotential %s not found in any of these paths:\n'%pseudo_filename
                raise ValueError(err_msg+ppstring)

            if verbose: print('cp %s %s'%(pseudo_filename,destpath))
            shutil.copy(pseudo_filename,destpath)

    def set_kpoints(self,kpoints,shiftk=[0,0,0]):
        """Add some logic to set the kpoints mesh"""
        #sanity check
        if len(kpoints) != 3: raise ValueError('Wrong kpoints dimensions')
        self.kpoints = kpoints
        self.shiftk = shiftk

    def copy(self):
        """Return a copy of this instance"""
        import copy
        return copy.deepcopy(self)

    def read_atomicspecies(self):
        lines = iter(self.file_lines)
        #find ATOMIC_SPECIES keyword in file and read next line
        for line in lines:
            if "ATOMIC_SPECIES" in line:
                for i in range(int(self.system["ntyp"])):
                    atype, mass, psp = next(lines).split()
                    self.atypes[atype] = [mass,psp]

    def get_symmetry_spglib(self):
        """
        get the symmetry group of this system using spglib
        """
        import spglib

        lat, positions, atypes = self.get_cell()
        lat = np.array(lat)

        at = np.unique(atypes)
        an = dict(list(zip(at,list(range(len(at))))))
        atypes = [an[a] for a in atypes]

        cell = (lat,positions,atypes)

        spacegroup = spglib.get_spacegroup(cell,symprec=1e-5)
        return spacegroup

    def get_masses(self):
        """ Get an array with the masses of all the atoms
        """
        masses = []
        for atom in self._atoms:
            atype = self.atypes[atom[0]]
            mass = float(atype[0])
            masses.append(mass)
        return masses

    def set_path(self,path):
        self.klist = path.get_klist()

    def get_cell(self):
        """ Get the lattice parameters, postions of the atoms and chemical symbols
        """
        cell = self.cell_parameters
        sym = [atom[0] for atom in self._atoms]
        pos = [atom[1] for atom in self._atoms]
        if self.atomic_pos_type == 'bohr':
            pos = car_red(pos,cell)
        return cell, pos, sym

    def set_atoms_string(self,string):
        """
        set the atomic postions using string of the form
        Si 0.0 0.0 0.0
        Si 0.5 0.5 0.5
        """
        atoms_str = [line.strip().split() for line in string.strip().split('\n')]
        atoms = []
        for atype,x,y,z in atoms_str:
            atoms.append([atype,list(map(float,[x,y,z]))])
        self._atoms = atoms

    def set_atoms_ase(self,atoms):
        """ set the atomic postions using a Atoms datastructure from ase
        """
        # we will write down the cell parameters explicitly
        self.ibrav = 0
        self.cell_parameters = atoms.get_cell()
        self._atoms = list(zip(atoms.get_chemical_symbols(),atoms.get_scaled_positions()))

    def displace(self,cart_mode,displacement,masses=None):
        """ Displace the atoms acoording to a phonon mode """
        import copy
        #normalize with masses
        if masses is None: masses = self.get_masses()
        if len(masses) != self.natoms: raise ValueError('Wrong dimensions of the masses list')

        #apply displacement
        atomic_car_pos_0 = self.atomic_car_pos
        atoms_car_pos_disp = []
        for i,(atype,apos) in enumerate(self._atoms):
            delta = cart_mode[i].real*displacement/sqrt(masses[i])
            atom = [atype, atomic_car_pos_0[i]+delta]
            atoms_car_pos_disp.append( atom )

        #store displaced structures
        self.set_atoms( atoms_car_pos_disp, coordtype="cartesian" )
        
    @property    
    def atomic_red_pos(self):
        pos = []
        for i in range(self.natoms):
            pos.append(self._atoms[i][1])
        return pos

    @property
    def atomic_car_pos(self):
        pos = []
        for i in range(self.natoms):
            red_pos = self._atoms[i][1]
            pos.append(red_car([red_pos],self.cell_parameters)[0])
        return pos

    @property
    def atoms(self):
        return self._atoms

    def get_displaced(self,cart_mode,displacement,masses=None):
        """ Create a copy and displace along the phonon mode """
        copy = self.copy()
        copy.displace(cart_mode,displacement,masses=masses)
        return copy

    def read_atoms(self):
        lines = iter(self.file_lines)
        #find READ_ATOMS keyword in file and read next lines
        for line in lines:
            if "ATOMIC_POSITIONS" in line:
                atomic_pos_type = line
                self.atomic_pos_type = re.findall('([A-Za-z]+)',line)[-1]
                atoms = []
                for i in range(int(self.system["nat"])):
                    atype, x,y,z = next(lines).split()
                    atoms.append([atype,[float(i) for i in (x,y,z)]])
        self._atoms = atoms
        self.atomic_pos_type = atomic_pos_type.replace('{','').replace('}','').strip().split()[1]

    @property
    def alat(self):
        if self.ibrav == 0:
            return np.linalg.norm(self.cell_parameters[0])
        else:
            return self.system['celldm(1)']

    @property
    def cell_parameters(self):
        if self.ibrav == 0:
            return self._cell_parameters
        elif self.ibrav == 1:
            a = float(self.system['celldm(1)'])
            cell_parameters = [[  a,   0,   0],
                               [  0,   a,   0],
                               [  0,   0,   a]]
        elif self.ibrav == 2:
            a = float(self.system['celldm(1)'])
            cell_parameters = [[ -a/2,   0, a/2],
                               [    0, a/2, a/2],
                               [ -a/2, a/2,   0]]
        elif self.ibrav == 3:
            a = float(self.system['celldm(1)'])
            cell_parameters = [[ a/2,  a/2,  a/2],
                               [-a/2,  a/2,  a/2],
                               [-a/2, -a/2,  a/2]]
        elif self.ibrav == 4:
            a = float(self.system['celldm(1)'])
            c = float(self.system['celldm(3)'])
            cell_parameters = [[   a,          0,  0],
                               [-a/2,sqrt(3)/2*a,  0],
                               [   0,          0,c*a]]
        elif self.ibrav == 6:
            a = float(self.system['celldm(1)'])
            c = float(self.system['celldm(3)'])
            cell_parameters = [[  a,   0,   0],
                               [  0,   a,   0],
                               [  0,   0, c*a]]
        else:
            raise NotImplementedError('ibrav = %d not implemented'%self.ibrav)
        return cell_parameters 

    @cell_parameters.setter
    def cell_parameters(self,value):
        self._cell_parameters = value

    @property
    def ibrav(self):
        return int(self.system['ibrav'])

    @ibrav.setter
    def ibrav(self,value):
        if not hasattr(self,'_cell_parameters') and value == 0: 
            raise ValueError('Must set cell_parameters before setting ibrav to 0')
        if value == 0: self.remove_key(self.system,'celldm(1)')
        self.system['ibrav'] = value

    def read_cell_parameters(self):
        """read the cell parameters from the input file """
        def rmchar(string,symbols): return ''.join([c for c in string if c not in symbols])

        if self.ibrav == 0:
            if 'celldm(1)' in list(self.system.keys()):
                a = float(self.system['celldm(1)'])
            else:
                a = 1
            lines = iter(self.file_lines)
            for line in lines:
                if "CELL_PARAMETERS" in line:
                    units = rmchar(line.strip(),'{}()').split()
                    cell_parameters = [[],[],[]]
                    if len(units) > 1:
                        self.cell_units = units[1]
                    else:
                        self.cell_units = 'bohr'
                    for i in range(3):
                        cell_parameters[i] = [ float(x)*a for x in next(lines).split() ]
            if self.cell_units == 'angstrom' or self.cell_units == 'bohr':
                if 'celldm(1)' in self.system: del self.system['celldm(1)']
            if 'celldm(1)' not in list(self.system.keys()):
                a = np.linalg.norm(cell_parameters[0])
            self._cell_parameters = cell_parameters
        
    def read_kpoints(self):
        lines = iter(self.file_lines)
        #find K_POINTS keyword in file and read next line
        for line in lines:
            if "K_POINTS" in line:
                #chack if the type is automatic
                if "automatic" in line:
                    self.ktype = "automatic"
                    vals = list(map(float, next(lines).split()))
                    self.kpoints, self.shiftk = vals[0:3], vals[3:6]
                #otherwise read a list
                else:
                    #read number of kpoints
                    nkpoints = int(next(lines).split()[0])
                    self.klist = []
                    self.ktype = ""
                    try:
                        lines_list = list(lines)
                        for n in range(nkpoints):
                            vals = lines_list[n].split()[:4]
                            self.klist.append( list(map(float,vals)) )
                    except IndexError:
                        print("wrong k-points list format")
                        exit()

    def slicefile(self, keyword):
        file_slice_regexp = '&%s(?:.?)+\n((?:.+\n)+?)(?:\s+)?[\/&]'%keyword
        lines = re.findall(file_slice_regexp,"".join(self.file_lines),re.MULTILINE)
        return lines

    def store(self,group,name):
        """
        Save the variables specified in each of the groups on the structure
        """
        group_regexp = '([a-zA-Z_0-9_\(\)]+)(?:\s+)?=(?:\s+)?([a-zA-Z/\'"0-9_.-]+)'
        for file_slice in self.slicefile(name):
            for keyword, value in re.findall(group_regexp,file_slice):
                group[keyword.strip()]=value.strip()

    def stringify_group(self, keyword, group):
        if group != {}:
            string='&%s\n' % keyword
            for keyword in sorted(group): # Py2/3 discrepancy in keyword order
                string += "%20s = %s\n" % (keyword, group[keyword])
            string += "/&end"
            return string
        else:
            return ''

    def remove_key(self,group,key):
        """ if a certain key exists in the group, remove it """
        if key in list(group.items()):
            del group[key]

    def write(self,filename):
        """write the file to disk """
        with open(filename,'w') as f:
           f.write(str(self))

    def get_string(self):
        """
        Output the file in the form of a string
        """
        lines = []; app = lines.append
        app( self.stringify_group("control",self.control) ) #print control
        app( self.stringify_group("system",self.system) ) #print system
        app( self.stringify_group("electrons",self.electrons) ) #print electrons
        app( self.stringify_group("ions",self.ions) ) #print ions
        app( self.stringify_group("cell",self.cell) ) #print ions

        #print atomic species
        app( "ATOMIC_SPECIES" )
        for atype in self.atypes:
            app( " %3s %8s %20s" % (atype, self.atypes[atype][0], self.atypes[atype][1]) )

        #print atomic positions
        app( "ATOMIC_POSITIONS { %s }"%self.atomic_pos_type )
        for atom in self._atoms:
            app( "%3s %14.10lf %14.10lf %14.10lf" % (atom[0], atom[1][0], atom[1][1], atom[1][2]) )

        #print kpoints
        if self.ktype == "automatic":
            app( "K_POINTS { %s }" % self.ktype )
            app( ("%3d"*6)%tuple(self.kpoints + self.shiftk) )
        else:
            app( "K_POINTS { %s }" % self.ktype )
            app( "%d" % len(self.klist) )
            for kpt in self.klist:
                app( ("%12.8lf "*4)%tuple(kpt) )

        #print cell parameters
        if self.ibrav == 0:
            app( "CELL_PARAMETERS %s"%self.cell_units )
            app( ("%14.10lf "*3)%tuple(self.cell_parameters[0]) )
            app( ("%14.10lf "*3)%tuple(self.cell_parameters[1]) )
            app( ("%14.10lf "*3)%tuple(self.cell_parameters[2]) )
        return "\n".join(lines)

    def __str__(self):
        return self.get_string()
