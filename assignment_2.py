import os
import numpy as np
import sys


def singleFlow():
    protocolArray = ['Tahoe', 'Reno', 'Newreno', 'Vegas']
    for protocol in protocolArray:
        for i in list(np.arange(1, 10.5, 0.5)):
            os.popen('ns ex_1.tcl ' + "{" + protocol + "}" + " " + str(i))


def doubleFlow():
    pair_1 = ('Reno','Reno')
    pair_2 = ('Newreno','Reno')
    pair_3 = ('Vegas','Vegas')
    pair_4 = ('Newreno','Vegas')
    pairArray = [pair_1, pair_2, pair_3, pair_4]
    for protocol_pair in pairArray:
        for i in list(np.arange(1, 10.5, 0.5)):
            os.popen('ns ex_2.tcl ' + "{" + protocol_pair[0] + "}" + " " + "{" + protocol_pair[1] + "}" + " " + str(i))


def queueing():
    pair_1 = ('Reno','DropTail')
    pair_2 = ('Reno','RED')
    pair_3 = ('Sack1','DropTail')
    pair_4 = ('Sack1','RED')
    pairArray = [pair_1, pair_2, pair_3, pair_4]
    for protocol_pair in pairArray:
        os.popen('ns ex_3.tcl ' + "{" + protocol_pair[0] + "}" + " " + "{" + protocol_pair[1] + "}")
        

if len(sys.argv) > 1:
    if sys.argv[1] == '1':
        singleFlow()
    elif sys.argv[1] == '2':
        doubleFlow()
    elif sys.argv[1] == '3':
        queueing()
else:
    # if no arguments are specified then run all the experiments
    singleFlow()
    doubleFlow()
    queueing()
