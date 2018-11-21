# Copyright (c) 2018, Henrique Miranda
# All rights reserved.
#
# This file is part of the yambopy project
#
import numpy as np
from yambopy.tools.string import marquee
from yambopy.plot.plotting import add_fig_kwargs
from qepy.lattice import Path

class YambopyBandStructure():
    """
    Class to plot bandstructures
    """
    _colormap = 'rainbow'

    def __init__(self,bands,kpoints,kpath=None,fermie=0,weights=None,**kwargs):
        self.bands = np.array(bands)
        self.weights = np.array(weights) if weights is not None else None
        self.kpoints = np.array(kpoints)
        self.kwargs = kwargs
        self.kpath = kpath
        self.fermie = fermie
        self._xlim = None
        self._ylim = None

    @property
    def nbands(self):
        nkpoints, nbands = self.bands.shape
        return nbands

    @property
    def nkpoints(self):
        nkpoints, nbands = self.bands.shape
        return nkpoints

    @property
    def xlim(self):
        if self._xlim is None: return (min(self.distances),max(self.distances))
        return self._xlim

    @property
    def ylim(self):
        if self._ylim is None: return (np.min(self.bands)-self.fermie,np.max(self.bands)-self.fermie)
        return self._ylim

    @classmethod
    def from_dict(cls,d):
        path = Path.from_dict(d['kpath'])
        instance = cls(d['bands'],d['kpoints'],kpath=path,
                       fermie=d['fermie'],weights=d['weights'],**d['kwargs'])
        instance._xlim = d['_xlim']
        instance._ylim = d['_ylim']
        return instance

    @classmethod
    def from_json(cls,filename):
        import json
        with open(filename,'r') as f:
            d = json.load(f)
        return cls.from_dict(d)

    def as_dict(self):
        """ Return the data of this object as a dictionary
        """
        d = { 'bands': self.bands.tolist(),
              'weights': self.weights.tolist() if self.weights is not None else None,
              'kpoints': self.kpoints.tolist(),
              'kwargs': self.kwargs,
              'kpath': self.kpath.as_dict(),
              'fermie': self.fermie,
              '_xlim': self._xlim,
              '_ylim': self._ylim }
        return d 

    def write_json(self,filename):
        """serialize this class as a json file"""
        import json
        with open(filename,'w') as f:
            json.dump(self.as_dict(),f)

    def set_fermi(self,valence):
        """simple function to set the fermi energy given the number of valence bands
        """
        self.fermie = np.max(self.bands[:,valence-1])
        self.set_ylim(None)

    def set_xlim(self,xlim):
        self._xlim = xlim

    def set_ylim(self,ylim):
        self._ylim = ylim

    def set_ax_lim(self,ax,fermie=0,ylim=None,xlim=None):
        if xlim is None: xlim = self.xlim
        if ylim is None: ylim = self.ylim
        ax.set_xlim(xlim[0],xlim[1])
        ax.set_ylim(ylim[0]-self.fermie,ylim[1]-self.fermie)

    @property
    def distances(self):
        if not hasattr(self,"_distances"):
            self._distances = [0]
            distance = 0
            for nk in range(1,len(self.kpoints)):
                distance += np.linalg.norm(self.kpoints[nk]-self.kpoints[nk-1])
                self._distances.append(distance)
        return self._distances

    def as_list(self,bands=None):
        yl = YambopyBandStructureList([self])
        if bands: yl.append(bands)
        return yl

    @add_fig_kwargs    
    def plot(self):
        """return a matplotlib figure with the plot"""
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        self.plot_ax(ax)
        return fig

    def set_kwargs(self,**kwargs):
        self.kwargs.update(kwargs)

    def get_kwargs(self,**kwargs):
        from copy import deepcopy
        fullkwargs = deepcopy(self.kwargs)
        fullkwargs.update(kwargs)
        return fullkwargs

    def add_kpath_labels(self,ax):
        """
        Add vertical lines at the positions of the high-symmetry k-points
        """
        if self.kpath is None:
            ax.xaxis.set_ticks([])
            return 
        for kpoint, klabel, distance in self.kpath:
            ax.axvline(distance,c='k')
        self.kpath.set_xticks(ax)

    def plot_ax(self,ax,xlim=None,ylim=None,ylabel='$\epsilon_{n\mathbf{k}}$ [eV]',
                alpha_weights=0.5,legend=False,**kwargs):
        """Receive an intance of matplotlib axes and add the plot"""
        kwargs = self.get_kwargs(**kwargs)
        fermie = kwargs.pop('fermie',self.fermie)
        size = kwargs.pop('size',1)
        c = kwargs.pop('c',None)
        c_weights = kwargs.pop('c_weights',c)
        for ib,band in enumerate(self.bands.T):
            x = self.distances
            y = band-fermie
            ax.plot(x,y,c=c,**kwargs)
            if self.weights is not None:
                dy = self.weights[:,ib]*size
                ax.fill_between(x,y+dy,y-dy,alpha=alpha_weights,color=c_weights,linewidth=0)
            kwargs.pop('label',None)
        self.set_ax_lim(ax,fermie=fermie,xlim=xlim,ylim=xlim)
        ax.set_ylabel(ylabel)
        self.add_kpath_labels(ax)
        if legend: ax.legend()
    
    def __add__(self,y):
        """Add the bands of two systems together"""
        #add some consistency check
        bands = self.bands + y.bands
        return YambopyBandStructure(bands,self.kpoints,kpath=self.kpath,fermie=self.fermie+y.fermie,**self.kwargs)
 
    def __sub__(self,y):
        """Subtract the bands of two systems together"""
        #add some consistency check
        bands = self.bands - y.bands
        return YambopyBandStructure(bands,self.kpoints,kpath=self.kpath,fermie=self.fermie-y.fermie,**self.kwargs)

    def __mul__(self,y):
        """Scale the bands of the system"""
        #add some consistency check
        bands = self.bands*y
        return YambopyBandStructure(bands,self.kpoints,kpath=self.kpath,fermie=self.fermie*y,**self.kwargs)

    def __truediv__(self,y):
        """Scale the bands of the system"""
        #add some consistency check
        bands = self.bands/y
        return YambopyBandStructure(bands,self.kpoints,kpath=self.kpath,fermie=self.fermie/y,**self.kwargs)
    
    def __str__(self):
        lines = []; app = lines.append
        app('nkpoints: %d'%self.nkpoints)
        app('nbands: %d'%self.nbands)
        app('has kpath: %s'%hasattr(self,'kpath'))
        return "\n".join(lines)

class YambopyBandStructureList():
    """This class contains a list of band-structure classes and is responsible for plotting them together"""
    def __init__(self,bandstructures):
        self.bandstructures = bandstructures

    @classmethod
    def from_pickle(cls,filename):
        import pickle
        with open(filename,'rb') as f:
            ybs = pickle.load(f)
        return ybs

    @property
    def has_legend(self):
        return any(['label' in bandstructure.kwargs for bandstructure in self.bandstructures])

    @property
    def nbandstructures(self):
        return len(self.bandstructures)

    @property
    def xlim(self):
        low_xlim = [bandstructure.xlim[0] for bandstructure in self.bandstructures]
        top_xlim = [bandstructure.xlim[1] for bandstructure in self.bandstructures]
        return (np.min(low_xlim),np.max(top_xlim))

    @property
    def ylim(self):
        low_ylim = [bandstructure.ylim[0] for bandstructure in self.bandstructures]
        top_ylim = [bandstructure.ylim[1] for bandstructure in self.bandstructures]
        return (np.min(low_ylim),np.max(top_ylim))

    def as_dict(self):
        bandstructures_dict=[]
        for bandstructure in self.bandstructures:
            bandstructures_dict.append(bandstructure.as_dict())
        return bandstructures_dict

    @classmethod
    def from_json(cls,filename):
        import json
        with open(filename,'r') as f:
            d = json.load(f)
        return cls.from_dict(d)

    @classmethod
    def from_dict(cls,d):
        bandstructures = []
        for bandstructure_dict in d:
            bandstructure = YambopyBandStructure.from_dict(bandstructure_dict)
            bandstructures.append(bandstructure)
        return cls(bandstructures)

    def __getitem__(self,idx):
        return self.bandstructures[idx]
    
    def append(self,bands):
        if isinstance(bands,list): self.bandstructure.extend(bands)
        self.bandstructures.append(bands)

    def add_bandstructure(self,bandstructures,**kwargs):
        """
        Add a bandstructure to bandstructure set
        """
        if not isinstance(bandstructures,list): bandstructures = [bandstructures]

        #add arguments in all the structures
        for bandstructure in bandstructures:
            bandstructure.kwargs.update(kwargs)

        #extend current bandstructure set
        self.bandstructures.extend(bandstructures)

    def plot_ax(self,ax,legend=True,xlim=None,ylim=None,**kwargs):
        title = kwargs.pop('title',None)
        for i,bandstructure in enumerate(self.bandstructures):
            bandstructure.plot_ax(ax,**kwargs)
        if xlim is None: ax.set_xlim(self.xlim)
        else:            ax.set_xlim(xlim)
        if ylim is None: ax.set_ylim(self.ylim)
        else:            ax.set_ylim(ylim)
        if title: ax.set_title(title)
        if legend and self.has_legend: ax.legend()

    def set_fermi(self,valence):
        """Find the Fermi energy of all the bandstructures by shifting the Fermi energy"""
        for bandstructure in self.bandstructures:
            bandstructure.set_fermi(valence)

    @add_fig_kwargs
    def plot(self,**kwargs):
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        self.plot_ax(ax,**kwargs)
        return fig
    
    def get_color(self,i,colormap='gist_rainbow'):
        colormap = self.get_colormap(colormap=colormap) 
        return colormap[i]

    def get_colormap(self,colormap='gist_rainbow'):
        """get a list of colors for each plot"""
        import matplotlib.pyplot as plt
        cmap = plt.get_cmap(colormap) #get color map
        return [cmap(i) for i in np.linspace(0, 1, self.nbandstructures)]

    def write_json(self,filename):
        """serialize this class as a json file"""
        import json
        with open(filename,'w') as f:
            json.dump(self.as_dict(),f)

    def pickle(self,filename):
        import pickle
        with open(filename,'wb') as f:
            pickle.dump(self,f)

    def __str__(self):
        lines = []; app = lines.append
        app(marquee(self.__class__.__name__))
        app('nbandstructures: %d'%self.nbandstructures)
        return "\n".join(lines)
