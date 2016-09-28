#
# Author: Henrique Pereira Coutada Miranda
# Example script to plot the weigth of the atomic species in the bandstructure
#
from qepy import *
import sys
import argparse
import matplotlib.pyplot as plt

folder = 'bands'

p = Path([ [[0.0, 0.0, 0.0],'G'],
           [[0.5, 0.0, 0.0],'M'],
           [[1./3,1./3,0.0],'K'],
           [[0.0, 0.0, 0.0],'G']], [100,50,100])

#parse options
parser = argparse.ArgumentParser(description='Test the yambopy script.')
parser.add_argument('-c' ,'--calc',    action="store_true", help='Project orbitals')
parser.add_argument('-a' ,'--analyse', action="store_true", help='Analyse data')
parser.add_argument('-p' ,'--plot',    action="store_true", help='Analyse data')
args = parser.parse_args()

if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)

if args.calc:
    f = open('proj.in','w')
    projwfc = ProjwfcIn('mos2')
    projwfc.write(folder=folder)
    projwfc.run(folder=folder)

if args.analyse:
    pxml = ProjwfcXML('mos2',path=folder)
    # obtain the list of orbitals and quantum numbers
    print pxml
    print "Writting projections"
    pxml.write_proj()
    print "done!"

if args.plot:
    pxml = ProjwfcXML('mos2',path=folder)
    print pxml

    # select orbitals to plot
    # example1 mo, s2 and mos2
    mo = list(xrange(16))     #list containing the indexes of all the orbitals of mo
    s  = list(xrange(16,48))  #list containing the indexes of all the orbitals of s

    fig = plt.figure(figsize=(30,10))
    for n,(orb,title) in enumerate(zip([mo,s,mo+s],['mo','s','mos2'])):
        ax = plt.subplot(1,3,n+1)
        plt.title(title)
        pxml.plot_eigen(ax,path=p,selected_orbitals=orb)
        ax.set_ylim([-7,6])
    plt.show()
    