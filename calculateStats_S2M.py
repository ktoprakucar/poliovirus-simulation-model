######################################################################################################
#
# Name: calculateStats_S2M.py
# Author: C Zhou
# Date of Origination: 3 December 2015
# Summary:  This script parses report output from S2M (aka Qspp_main.exe) and for each result value, each passage, calculates the min, max, mean, median, and standard deviation values. 
# Application:  This script was written for generating graphs from simulations. 
# Project:  LDRD - publication of code developed during Qspp LDRD project.
#
# License:  See LICENSE.md for license information.
#
#######################################################################################################

import sys
import string
import copy
import re, os
import subprocess
#from subprocess import call
import simulation

##### CONSTANTS and CONFIGURABLES

DATA_DIR = "/Users/zhou4/DEV/Virus/Simulations/Run_of_3Dec2015/Reportfiles/"
STAT_DIR = "/Users/zhou4/DEV/Virus/Simulations/Run_of_3Dec2015/Statfiles/"

##### PATTERNS

# Note: Patterns are specific to structure of data filenames
# Note: Listed are those parameters that have been varied thus far in simulation
# Sample filename format 1:  fitness2-r6-s2-a2-e0.01_rep5.report  # 5th replicate
# Sample filename format 2:  fit2_r6_s2_a2_e0.01.report5          # 5th replicate

#NAME_FORMAT_1 = True; NAME_FORMAT_2 = False; NAME_FORMAT_3 = False 
#NAME_FORMAT_1 = False; NAME_FORMAT_2 = True; NAME_FORMAT_3 = False
NAME_FORMAT_1 = False; NAME_FORMAT_2 = False; NAME_FORMAT_3 = True

if NAME_FORMAT_1:
    p_report        = re.compile('[Rr]eport') 
    p_fitness       = re.compile('[Ff]itness(\d)')
    p_recombination = re.compile('-r(\d)')
    p_synergy       = re.compile('-s(\d)')
    p_error         = re.compile('-e(\.\d+)')
    p_accelerator   = re.compile('-a(\d)')
    p_replicate     = re.compile('[Rr]ep(\d+)')
    p_default       = re.compile('[Dd]efault')

if NAME_FORMAT_2:
    p_report        = re.compile('[Rr]eport')  
    p_fitness       = re.compile('[Ff]it(\d)')
    p_recombination = re.compile('_r(\d)')
    p_synergy       = re.compile('_s(\d)')
    p_error         = re.compile('_e(\d\.\d+)')
    p_accelerator   = re.compile('_a(\d)')
    p_replicate     = re.compile('[Rr]eport(\d+)')
    p_default       = re.compile('[Dd]efault')

if NAME_FORMAT_3:  # Same as NAME_FORMAT_1 so far...
    p_report        = re.compile('[Rr]eport') 
    p_fitness       = re.compile('[Ff]itness(\d)')
    p_recombination = re.compile('-r(\d)')
    p_synergy       = re.compile('-s(\d)')
    p_error         = re.compile('-e(\.\d+)')
    p_accelerator   = re.compile('-a(\d)')
    p_replicate     = re.compile('[Rr]ep(\d+)')
    p_default       = re.compile('[Dd]efault')


# FILES

SCRIPT     = "calculateStats_S2M"
SCRIPT_PY  = SCRIPT + ".py"
logFile    = "./" + SCRIPT + ".log"
outFile    = "./" + SCRIPT + ".out"

LOGFILE    = open(logFile,"w")
OUTFILE    = open(outFile,"w")

# HELP STRINGS and CONSTANTS

HELP_STRING  = "Description: Script " + SCRIPT_PY + " parses output from S2M simulations.\nRun this script from the PythonCode/ directory.\nType: python " + SCRIPT_PY + " usage, for more information."

USAGE_STRING = "Usage:  " + SCRIPT_PY + " <simulation_directory>\nSpecification of the simulation directory is optional: you may use the default,\nor change it by fully specifying a pathname to your directory of choice\n" 

INPUT_STRING = "Input:  The input simulation directory contains a set of report files generated by S2M.\nEach filename is structured as, \'fitnessN-a3-b2-c1_repM.report\', where a-3,b-2,c-1,etc are input parameters to S2M, and repM is the Mth replicate of the simulation run. \'fitnessN\' specifies which fitness grid was used (e.g., fitness1, fitness2)."

ARG_COUNT = (1,2)  # 0th is code name, 1st is 'help' string or name of target directory
CHATTY    = True  # When True, informative statements will be printed
#CHATTY    = False  # When True, informative statements will be printed

##### DATA STRUCTURES

reportFiles       = { # "outer" list of grouped simulation report files
    "fitness1"       : [], # Using fitness1 and default parameters (no DIPs)
    "fitness2"       : [], # Using fitness2 and default parameters (w/DIPs)
    "recombination"  : [], # Varying the rate of recombination
    "synergy"        : [], # Varying Mahoney synergy
    "error"          : [], # Varying replication error rate
    "accelerator"    : [], # Varying fitness accelerator
}

simListTemplate = []
simulationList = []

##### FUNCTIONS

def GetReps(sim,fileList):
    simList = copy.deepcopy(simListTemplate)
    for file in fileList:
        match = re.search(sim,file)
        if match:
            simList.append(file)
    #print "Exiting GetRepts, simList is:", simList
    return simList


##### Get input parameter(s) 

# These stay as defined unless user inputs a different value
dataDir = DATA_DIR
statDir = STAT_DIR

argCount = len(sys.argv)
LOGFILE.write("%s%s\n" % ("argCount is ", argCount))

if argCount >= 2:
    match = re.search("^help$", sys.argv[1].lower())
    if match:
        print HELP_STRING
        exit(0)
    match = re.search("^input$", sys.argv[1].lower())
    if match:
        print INPUT_STRING
        exit(0)
    match = re.search('^usage$', sys.argv[1].lower())
    if match:
        print USAGE_STRING
        exit(0)
    dataDir = sys.argv[1]  # If user changes default, they must fully qualify pathname
    if argCount == 3:
        statDir = sys.argv[2] # need fully qualified pathname

LOGFILE.write("%s%s\n" % ("Processing files from directory ", dataDir))

# Reflect parameters

if CHATTY:
    print "Files from this directory will be parsed: ", dataDir

##### Get listing of user's data files

p = subprocess.Popen(['ls',dataDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
LOGFILE.write("%s%s\n" % ("System Err result of listing user dir is: ",err))
fileList = out.split('\n')

# Filter to capture only report files
reportFileList = []
for file in fileList:
    match = re.search(p_report,file)
    if match:
        reportFileList.append(file)

if CHATTY:
    print "These report files will be processed:"
    for file in reportFileList:
        print file,
    print

LOGFILE.write("\nThese report files will be processed:\n")
for file in reportFileList:
    LOGFILE.write("%s\n" % (file))

# Group files comprising replicates 

# NOTE:  Code assumes that only one parameter is being varied at a time,
#   and this code is specific to the expected filenames for a specific simulation.

passageCount = 0

# Organize files
for file in reportFileList:
    match = re.search(p_recombination,file)
    if match:
        reportFiles["recombination"].append(file)
    match = re.search(p_synergy,file)
    if match:
        reportFiles["synergy"].append(file)
    match = re.search(p_error,file) 
    if match:
        reportFiles["error"].append(file)
    match = re.search(p_accelerator,file)
    if match:
        reportFiles["accelerator"].append(file)
    match = re.search(p_default,file)
    if match: 
        match = re.search(p_fitness,file)
        if match:
            if match.group(1) == '1':
                reportFiles["fitness1"].append(file)
            if match.group(1) == '2':
                reportFiles["fitness2"].append(file)

if CHATTY:
    print "Report files:"
    for key in reportFiles:
        print "   ", key, reportFiles[key]

LOGFILE.write("\nReport files\n")
for key in reportFiles:
    LOGFILE.write("%s%s%s\n" % (" * ", key, reportFiles[key]))

# Check data; capture distinct simulation names 

OK2PROCEED = True
FIRST      = True
passageCount = 0
checkPassageCount = 0
for key in reportFiles:
    for file in reportFiles[key]:
        # Capture number of passages (from data), and verify consistency
        pathFile = os.path.join(DATA_DIR,file) 
        p = subprocess.Popen(['wc',pathFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        match = re.search('\d+',out)
        if match:
            checkPassageCount = int(match.group(0)) - 2
            if FIRST:
                passageCount = checkPassageCount
                FIRST = False
        else:
            LOGFILE.write("%s%s\n" % ("ERROR: Problem in finding number of lines in file ", file))
            OK2PROCEED = False
        #print "There are", checkPassageCount, "passages in file", file
        if passageCount != checkPassageCount:
            LOGFILE.write("%s%s%s%s\n" % ("WARNING: inconsistency in passage count between files: file ",file," checkPassageCount ",checkPassageCount))
            OK2PROCEED = False

if passageCount <= 0:
    OK2PROCEED = False

print "OK to proceed:", OK2PROCEED, ", Number of passages is", passageCount

##### For each set of report files, group the replicates, then compute statistics and save to files

replicateSet = {
    "parameter" : "",
    "fileList"  : [],
} 
for key in reportFiles:
    parameterList = []     # eg, '-a1','-a2','-a3'
    replicateSetList = []  # A list of replicateSet dicts

    for filename in reportFiles[key]:  # First pass, collect parameters that were run
        if (key == "fitness1" or key == "fitness2"):
            parameter = "default" 
        else:
            if key == "recombination":
                match = re.search(p_recombination,filename)
            elif key == "synergy":
                match = re.search(p_synergy,filename)
            elif key == "accelerator":
                match = re.search(p_accelerator,filename)
            elif key == "error":
                match = re.search(p_error,filename)
            parameter = match.group(1)

        if parameter not in parameterList:   # Add to non-redundant list of parameter settings for this simulation
            parameterList.append(parameter)

    for parameter in parameterList:      # Create storage for each set of replicates (one set per parameter setting)
        nextReplicate = copy.deepcopy(replicateSet)
        nextReplicate["parameter"] = parameter
        replicateSetList.append(nextReplicate)

    print "parameterList is", parameterList

    for filename in reportFiles[key]:  # Second pass, group replicates (files) by parameter (ie, fill storage)
        if (key == "fitness1" or key == "fitness2"):
            parameter = "default" 
        else:
            if key == "recombination":
                match = re.search(p_recombination,filename)
            elif key == "synergy":
                match = re.search(p_synergy,filename)
            elif key == "accelerator":
                match = re.search(p_accelerator,filename)
            elif key == "error":
                match = re.search(p_error,filename)
            parameter = match.group(1)

        for replicate in replicateSetList:              # group each file in this simulation
            if replicate["parameter"] == parameter:     # group by parameter setting
                replicate["fileList"].append(filename)  # add to storage

    print "replicateSetList", replicateSetList 

    # Finally, for each parameter setting, compute summary statistics over the replicate set
    for parameter in parameterList:
        for replicate in replicateSetList:
            if replicate["parameter"] == parameter: 
                replicateFiles = replicate["fileList"]
                print "Calling simulation class with parameters:", passageCount, replicate["fileList"], dataDir, statDir, key, parameter
                sim = simulation.SimulationData(passageCount,replicate["fileList"],dataDir,statDir,key,parameter)
                sim.ProcessSimulationData()
                sim.PrintAll()
                sim.PrintAllStatistics2fileTabbed()

##### Clean up

OUTFILE.close()
LOGFILE.close()