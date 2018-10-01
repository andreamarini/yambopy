# Copyright (C) 2018 Henrique Pereira Coutada Miranda
# All rights reserved.
#
# This file is part of yambopy
#
"""
This file contains classes and methods to generate input files

The FiniteDifferencesPhononFlow
"""

from qepy.pw import PwIn
from qepy.ph import PhIn
from qepy.matdyn import Matdyn
from yambopy.tools.duck import isiter
from yambopy.flow import PwTask, PhTask, P2yTask, YamboTask, DynmatTask, YambopyFlow

__all__ = [
"FiniteDifferencesPhononFlow",
"KpointsConvergenceFlow",
"PwNscfYamboIPChiTasks",
"YamboQPBSETasks",
"PwNscfTask",
"PhPhononTask"
]

class FiniteDifferencesPhononFlow():
    """
    This class takes as an input one structure and a phonon calculation.
    It produces a flow with the QE input files displaced along the phonon modes

    Author: Henrique Miranda
    """
    def __init__(self,structure,phonon_modes):
        self.structure = structure
        if not isinstance(phonon_modes,Matdyn):
            raise ValueError('phonon_modes must be an instance of Matdyn')
        self.phonon_modes = phonon_modes

    def get_tasks(self,path,kpoints,ecut,nscf_bands,nscf_kpoints=None,
                  imodes_list=None,displacements=[0.01,-0.01],iqpoint=0,**kwargs):
        """
        Create a flow with all the tasks to perform the calculation
        
        Arguments:
            generator: a builder function that takes structure, kpoints, ecut, 
                       nscf_bands, nscf_kpoints and kwargs as argument and returns the
                       tasks to be performed at each displacement
        """

        if imodes_list is None: imodes_list = list(range(self.phonon_modes.nmodes))
        if not isiter(displacements): displacements = [displacements]
        generator = kwargs.pop("generator",PwNscfYamboIPChiTasks)
             
        #create qe input from structure
        pwin = PwIn.from_structure_dict(self.structure,kpoints=kpoints,ecut=ecut)

        tasks = []
        #
        # Undisplaced structure
        #
        tasks.extend(generator(pwin.get_structure(),kpoints,ecut,nscf_bands,nscf_kpoints,**kwargs))

        #
        # Displaced structures
        #
        for imode in imodes_list:
            #get phonon mode
            cart_mode = self.phonon_modes.modes[iqpoint,imode]
            #iterate over displacements
            for displacement in displacements:
                #displace structure
                input_mock = pwin.get_displaced(cart_mode, displacement=displacement)
                displaced_structure = input_mock.get_structure()

                #generate tasks
                new_tasks = generator(displaced_structure,kpoints,ecut,
                                      nscf_bands,nscf_kpoints,**kwargs)
                tasks.extend(new_tasks)

        return tasks

 
    def get_flow(self,path,kpoints,ecut,nscf_bands,nscf_kpoints=None,imodes_list=None,**kwargs):

        tasks = self.get_tasks(path=path,kpoints=kpoints,ecut=ecut,nscf_bands=nscf_bands,
                               nscf_kpoints=nscf_kpoints,imodes_list=imodes_list,**kwargs)
       
        #put all the tasks in a flow
        self.yambo_flow = YambopyFlow.from_tasks(path,tasks)
        return self.yambo_flow

    @property
    def path(self):
        return self.yambo_flow.path

class KpointsConvergenceFlow():
    """
    This class takes as an input one structure.
    It produces a flow with the QE input files with different number of kpoints
    and then runs a task staring from the QE input

    Author: Henrique Miranda
    """
    def __init__(self,structure):
        self.structure = structure
    
    def get_tasks(self,scf_kpoints,nscf_kpoints_list,ecut,nscf_bands,**kwargs):
        """
        Create a flow with all the tasks to perform the calculation
        
        Arguments:
            generator: a builder function that takes structure, kpoints, ecut, 
                       nscf_bands, nscf_kpoints and kwargs as argument and returns the
                       tasks to be performed at each displacement
        """
        generator = kwargs.pop("generator",PwNscfYamboIPChiTasks)

        #create a QE scf task and run
        qe_input = PwIn.from_structure_dict(self.structure,kpoints=scf_kpoints,ecut=ecut)
        qe_scf_task = PwTask.from_input(qe_input)
        tasks = [qe_scf_task]

        for nscf_kpoints in nscf_kpoints_list:

            #generate tasks
            new_tasks = generator(structure=self.structure,kpoints=scf_kpoints,
                                  nscf_kpoints=nscf_kpoints,
                                  ecut=ecut,nscf_bands=nscf_bands,**kwargs)
            tasks.extend(new_tasks)

        return tasks

    def get_flow(self,path,scf_kpoints,nscf_kpoints_list,ecut,nscf_bands,**kwargs):
        tasks = self.get_tasks(scf_kpoints=scf_kpoints,ecut=ecut,nscf_bands=nscf_bands,
                               nscf_kpoints_list=nscf_kpoints_list,**kwargs)
       
        #put all the tasks in a flow
        self.yambo_flow = YambopyFlow.from_tasks(path,tasks,**kwargs)
        return self.yambo_flow

def PwNscfYamboIPChiTasks(structure,kpoints,ecut,nscf_bands,
                          yambo_runlevel='-o c -V all',nscf_kpoints=None,**kwargs):
    """
    Return the PwNscfTasks and a YamboTask for and IP calculation
    """ 
    #create scf, nscf and p2y task
    tmp_tasks = PwNscfTasks(structure,kpoints,ecut,nscf_bands,nscf_kpoints)
    qe_scf_task,qe_nscf_task,p2y_task = tmp_tasks

    yambo_ip_default_dict = dict(QpntsRXd=[1,1],
                                 ETStpsXd=1000)
    yambo_ip_dict = kwargs.pop('yambo_ip_dict',yambo_ip_default_dict)

    #add yambo_task
    yambo_task = YamboTask.from_runlevel(p2y_task,yambo_runlevel,yambo_ip_dict,
                                                 dependencies=p2y_task)
    return qe_scf_task,qe_nscf_task,p2y_task,yambo_task


def YamboQPBSETasks(p2y_task,qp_dict,bse_dict,
                   qp_runlevel='-p p -g n -V all',bse_runlevel='-p p -k sex -y d -V all'):
    """
    Return a QP and BSE calculation
    """
    #create a yambo qp run
    qp_task = YamboTask.from_runlevel(p2y_task,qp_runlevel,qp_dict,dependencies=p2y_task)

    #create a yambo bse run
    bse_dict['KfnQPdb']="E < run/ndb.QP"
    bse_task = YamboTask.from_runlevel([p2y_task,qp_task],bse_runlevel,bse_dict,dependencies=qp_task)
    return qp_task, bse_task

def PhPhononTasks(structure,kpoints,ecut,qpoints=None):
    """
    Return a ScfTask, a PhTask and Matdyn task
    """

    #create a QE scf task and run
    qe_input = PwIn.from_structure_dict(structure,kpoints=kpoints,ecut=ecut)
    qe_scf_task = PwTask.from_input(qe_input)

    #create phonon tasks
    if qpoints is None: qpoints = qe_input.kpoints
    ph_input = PhIn.from_qpoints(qpoints)
    ph_task = PhTask.from_scf_task([ph_input,qe_scf_task],dependencies=qe_scf_task)

    #create matdyn task
    matdyn_task = DynmatTask.from_phonon_task(ph_task,dependencies=ph_task)
 
    return qe_scf_task, ph_task, matdyn_task

def PwNscfTasks(structure,kpoints,ecut,nscf_bands,nscf_kpoints=None):
    """
    Return a ScfTask, NscfTask and P2yTask preparing for a Yambo calculation
    """

    #create a QE scf task and run
    qe_input = PwIn.from_structure_dict(structure,kpoints=kpoints,ecut=ecut)
    qe_scf_task = PwTask.from_input(qe_input)

    #create a QE nscf task and run
    qe_input = qe_input.copy().set_nscf(nscf_bands,nscf_kpoints)
    qe_nscf_task = PwTask.from_input([qe_input,qe_scf_task],dependencies=qe_scf_task)

    #create a p2y nscf task and run
    p2y_task = P2yTask.from_nscf_task(qe_nscf_task)

    return qe_scf_task, qe_nscf_task, p2y_task
