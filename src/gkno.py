#!/usr/bin/python

from __future__ import print_function

from copy import deepcopy
import os.path
import getpass
import subprocess
import sys

import networkx as nx

import gkno.adminUtils
from gkno.adminUtils import *

import gkno.commandLine
from gkno.commandLine import *

import configurationClass.configurationClass
from configurationClass.configurationClass import *

import gkno.gknoErrors
from gkno.gknoErrors import *

import gkno.exportInstance
from gkno.exportInstance import *

import gkno.files
from gkno.files import *

import gkno.gknoConfigurationFiles
from gkno.gknoConfigurationFiles import *

import gkno.helpClass
from gkno.helpClass import *

import gkno.makefileData
from gkno.makefileData import *

import gkno.tracking
from gkno.tracking import *

import gkno.writeToScreen
from gkno.writeToScreen import *

__author__ = "Alistair Ward"
__version__ = "0.100"
__date__ = "July 2013"

def main():

  # Initialise variables:
  phoneHomeID = ''

  # Define the errors class.
  errors = gknoErrors()

  # Define the source path of all the gkno machinery.
  sourcePath = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno.py')]

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = adminUtils(sourcePath)

  # Define a configurationClass object.  This is part of the configurationClass library.  Also
  # define an object that handles finding configuration files for gkno (e.g. gkno specific
  # configuration file operations.
  config     = configurationMethods()
  gknoConfig = gknoConfigurationFiles()

  # Create a graph object.  This is a directed graph consisting of nodes representing the tasks
  # in the pipeline as well as data being fed into the nodes.  All relevant tool information
  # will be attached to the task nodes and information about the data is attached to the data
  # nodes.  The edges between the nodes define the command line argument for the data and tool.
  pipelineGraph = nx.DiGraph()

  # Define a command line options, get the first command line argument
  # and proceed as required.
  commands = commandLine()

  # Define a class for outputting graphics.
  draw = drawGraph()

  # Generate a class for storing details for use in the makefile.
  make = makefileData()

  # Define a help class.  This provides usage information for the user. Also define an object used
  # for writing to screen.
  gknoHelp = helpClass()
  write    = writeToScreen()

  # Get information on the mode being run. The pipelineName is the name of the pipeline
  # or the tool if being run in tool mode.
  admin.isRequested, admin.mode = commands.isAdminMode(admin.allModes)
  isPipeline                    = commands.setMode(admin.isRequested)
  runName                       = commands.getPipelineName(isPipeline)

  # Set the name of the pipeline/tool as a general attribute of the graph.
  pipelineGraph.graph['name']       = runName
  pipelineGraph.graph['isPipeline'] = isPipeline

  # Read in information from the gkno specific configuration file.
  gknoConfig.gknoConfigurationData = config.fileOperations.readConfigurationFile(sourcePath + '/config_files/gknoConfiguration.json')
  #TODO SORT OUT VALIDATION OF GKNO CONFIGURATION FILE>
  gknoConfig.validateConfigurationFile()
  gknoConfig.addGknoSpecificNodes(pipelineGraph, config, isPipeline)
  gknoConfig.eraseConfigurationData()

  # Check to see if gkno is being run in verbose mode or not.
  isVerbose = commands.checkVerbose(pipelineGraph, config, admin)

  # Each of the tools available to gkno should have a config file to describe its operation,
  #  purpose etc.  These are contained in config_files/tools.  Find all of the config files
  # and create a hash table with all available tools.
  # FIXME REMOVE TEMP
  gknoConfig.getJsonFiles(sourcePath + '/config_files/temp/')

  # Check if the pipeline/tool name is valid.
  if commands.mode != 'admin': gknoConfig.checkPipelineName(gknoHelp, isPipeline, runName)

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line. If help has been requested, print out the required
  # help.
  gknoHelp.checkForHelp(isPipeline, runName, admin, commands.mode)
  if gknoHelp.printHelp and not gknoHelp.specificPipelineHelp: gknoHelp.printUsage(pipelineGraph, config, gknoConfig, admin, sourcePath, runName)

  # Print gkno title and version to the screen.
  write.printHeader(__version__, __date__)

  # No admin mode requested. Prepare to setup our tool or pipeline run.
  if not admin.isRequested:

    # Make sure we've actually been "built" before doing any real processing.
    # Skip this requirement if we're only going to be printing a help message later.
    if not gknoHelp.printHelp and not admin.isBuilt():
      errors.gknoNotBuilt()
      errors.terminate()

    # If a pipeline is being run, check that configuration files exist for the selected
    # pipeline.  This should be in directory config_files and have the name <$ARGV[1]>.json.
    # If the file exists, parse the json file.
    if isPipeline:
      phoneHomeID               = 'pipes/' + runName
      #FIXME REMOVE TEMP
      pipelineFile              = sourcePath + '/config_files/temp/pipes/' + runName + '.json'
      pipelineConfigurationData = config.fileOperations.readConfigurationFile(pipelineFile)

      # TODO VALIDATION MODULE IS INCOMPLETE.  CONFIGURATIONCLASS NEEDS TO BE
      # MODIFIED TO INCLUDE THIS.
      instances = config.pipeline.processConfigurationData(pipelineConfigurationData, runName, gknoConfig.jsonFiles['tools'])

    # If gkno is being run in tool mode, set the phoneHomeID.
    else: phoneHomeID = 'tools/' + runName

  # Process all of the tool configuration files that are used.
  if commands.mode == 'pipeline':

    # Find all of the tasks to be used in the pipeline.
    for task in config.pipeline.taskAttributes:
      tool = config.pipeline.taskAttributes[task].tool

      # FIXME TEMPORARY LOCATION OF CONFIG FILES.  REMOVE TEMP WHEN COMPLETE.
      toolFile              = sourcePath + '/config_files/temp/tools/' + tool + '.json'
      toolConfigurationData = config.fileOperations.readConfigurationFile(toolFile)

      # TODO TOOL CONFIGURATION FILE VALIDATION HAS NOT YET BEEN HANDLED IN THE
      # CONFIGURATIONCLASS.
      # Ensure that the tool configuration file is well constructed and put all of the data
      # in data structures.  Each tool in each configuration file gets its own data structure.
      config.tools.processConfigurationData(tool, toolConfigurationData)
      del(toolConfigurationData)

    # For each task in the pipeline, build an individual graph consisting of a task node, input
    # option nodes (all input and output file arguments are treated as option nodes) and finally
    # all input and output files are given file nodes.  Nodes are merged later to generate the
    # final pipeline.
    config.buildTaskGraph(pipelineGraph, config.pipeline.taskAttributes.keys())

    # Attach additional information from the pipeline configuration file to the nodes.
    config.assignPipelineAttributes(pipelineGraph, config.pipeline.taskAttributes.keys())

    # Add the pipeline arguments to the nodeIDs dictionary.
    config.nodeMethods.getPipelineArgumentNodes(pipelineGraph, config)
  
    # Now that every task in the pipeline has an individual graph built, use the information
    # in the pipeline configuration file to merge nodes and build the final pipeline graph.
    config.mergeNodes(pipelineGraph)
  
    # Generate the workflow using a topological sort of the pipeline graph.
    config.pipeline.workflow = config.generateWorkflow(pipelineGraph)
  
    # Loop over all of the nodes and determine which require a value.  Also check to see if there
    # are missing edges.  For example, if a tool has an argument that is required, but is not included
    # in the pipeline configuration file (as a pipeline argument or via connections), the graph cannot
    # be completely defined.
    config.nodeMethods.setRequiredNodes(pipelineGraph, config.tools)

    # If help was requested on this specific pipeline, the information now exists to generate
    # the help information.
    if gknoHelp.specificPipelineHelp: gknoHelp.specificPipelineUsage(pipelineGraph, config, gknoConfig, runName, sourcePath)

  # If being run in the tool mode.
  elif commands.mode == 'tool':
    # FIXME TEMPORARY LOCATION OF CONFIG FILES.  REMOVE TEMP WHEN COMPLETE.
    toolFile              = sourcePath + '/config_files/temp/tools/' + runName + '.json'
    toolConfigurationData = config.fileOperations.readConfigurationFile(toolFile)

    # TODO TOOL CONFIGURATION FILE VALIDATION HAS NOT YET BEEN HANDLED IN THE
    # CONFIGURATIONCLASS.
    # Ensure that the tool configuration file is well constructed and put all of the data
    # in data structures.  Each tool in each configuration file gets its own data structure.
    instances = config.tools.processConfigurationData(runName, toolConfigurationData)
    del(toolConfigurationData)

    # Define the tasks structure. Since a single tool is being run, this is simply the name
    # of the tool. Set the tasks structure in the pipeline configuration object as well.
    config.pipeline.definePipelineAttributesForTool(runName)
    config.buildTaskGraph(pipelineGraph, config.pipeline.taskAttributes.keys())

  # Parse the command line and put all of the arguments into a list.
  if isVerbose: write.writeReadingCommandLineArguments()
  commands.getCommandLineArguments(pipelineGraph, config, gknoConfig, runName, isPipeline, isVerbose)
  if isVerbose: write.writeDone()

  # If help was requested or there were problems (e.g. the tool name or pipeline
  # name did not exist), print out the required usage information.
  if gknoHelp.printHelp and not gknoHelp.specificPipelineHelp:
    gknoHelp.printUsage(pipelineGraph, config, gknoConfig, admin, sourcePath, runName)

  # Populate the tl.arguments structure with the arguments with defaults from the tool configuration files.
  # The x.arguments structures for each of the classes used in gkno has the same format (a dictionary whose
  # keys are the names of tools: each tool is itself a dictionary of command line arguments, the value being
  # a list of associated parameters/files etc).  The command line in the makefile is then constructed from 
  # the x.arguments structures in a strict hierarchy.  tl.arguments contains the defaults found in the
  # configuration file.  These are overwritten (if conflicts occur) by the values in ins.arguments (i.e.
  # arguments drawn from the specified instance). Next, the cl.arguments are the commands defined on the
  # command line by the user and then finally, mr.arguments pulls information from the given multiple runs
  # file if one exists.

  # If admin mode requested, then run it & terminate script.
  # No need to bother with running tools or pipes.
  if admin.isRequested:
    success = admin.run(sys.argv)
    if success: exit(0)
    else: errors.terminate()
  
  # Print information about the pipeline to screen.
  if isPipeline and isVerbose: write.writePipelineWorkflow(pipelineGraph, config, gknoHelp)

  # Check if an instance was requested by the user.  If so, get the data and add the values to the data nodes.
  if isVerbose: write.writeCheckingInstanceInformation()
  instanceName = commands.getInstanceName()
  if isPipeline:
    #TODO REMOVE temp
    path               = sourcePath + '/config_files/temp/pipes/'
    availableInstances = gknoConfig.jsonFiles['pipeline instances']
  else:
    #TODO REMOVE temp
    path               = sourcePath + '/config_files/temp/tools/'
    availableInstances = gknoConfig.jsonFiles['tool instances']
  #TODO CHECK IF HELPCLASS FUNCTIONS ALREADY GET WHAT IS NEEDED.
  instanceData = config.getInstanceData(path, runName, instanceName, instances, availableInstances)
  # TODO Validate instance data. Check that tool instances have the argument field.

  # Check to see if any of the instance arguments are gkno specific arguments.
  gknoConfig.attachInstanceArgumentsToNodes(pipelineGraph, config, instanceData)

  # Now handle the rest of the instance arguments.
  if isPipeline: config.attachPipelineInstanceArgumentsToNodes(pipelineGraph, instanceData)
  else: config.attachToolInstanceArgumentsToNodes(pipelineGraph, instanceData, runName)
  if isVerbose: write.writeDone()

  # Attach the values of the pipeline arguments to the relevant nodes.
  #TODO USE attachToolArgumentsToNodes in attachPipelineArgumentsToNodes when dealing with tasks.
  if isVerbose: write.writeAssignPipelineArgumentsToNodes()
  if isPipeline: commands.attachPipelineArgumentsToNodes(pipelineGraph, config, gknoConfig)
  else: commands.attachToolArgumentsToNodes(pipelineGraph, config, gknoConfig)
  if isVerbose: write.writeDone()

  # Check if multiple runs or internal loops have been requested.
  hasMultipleRuns, hasInternalLoop = gknoConfig.hasLoop(pipelineGraph, config)
  if hasMultipleRuns or hasInternalLoop:
    if isVerbose: write.writeAssignLoopArguments(hasMultipleRuns)
    gknoConfig.addLoopValuesToGraph(pipelineGraph, config)
    if isVerbose: write.writeDone()

  # TODO DEAL WITH INSTANCE EXPORTS
  # If the --export-config has been set, then the user is attempting to create a
  # new configuration file based on the selected pipeline.  This can only be
  # selected for a pipeline and if multiple runs are NOT being performed.
  #if '--export-instance' in cl.uniqueArguments:
    #if mr.hasMultipleRuns:
    #  er.exportInstanceForMultipleRuns(verbose)
    #  er.terminate()

    # Define the json export object, initialise and then check that the given filename is unique.
    #make.arguments = deepcopy(make.coreArguments)
    #make.prepareForInternalLoop(iLoop.tasks, iLoop.arguments, iLoop.numberOfIterations)
    #ei = exportInstance()
    #if pl.isPipeline: ei.checkInstanceFile(cl.argumentList, pl.pipelineName, pl.instances, verbose)
    #else: ei.checkInstanceFile(cl.argumentList, pl.pipelineName, tl.instances[tl.tool], verbose)
    #ei.getData(gknoHelp, tl.argumentInformation, tl.shortForms, pl.isPipeline, pl.workflow, pl.taskToTool, pl.argumentInformation, pl.arguments, pl.toolsOutputtingToStream, pl.toolArgumentLinks, pl.linkage, make.arguments, verbose)
    #if pl.isPipeline: ei.writeNewConfigurationFile(sourcePath, 'pipes', ins.externalInstances, pl.instances, cl.linkedArguments)
    #else: ei.writeNewConfigurationFile(sourcePath, 'tools', ins.externalInstances, tl.instances[tl.tool], cl.linkedArguments)

    # After the configuration file has been exported, terminate the script.  No
    # Makefile is generated and nothing is executed.
    #exit(0)
 
  # Now that the command line argument has been parsed, all of the values supplied have been added to the
  # option nodes.  All of the file nodes can take their values from their corresponding option nodes.
  commands.mirrorFileNodeValues(pipelineGraph, config)

  # Construct all filenames.  Some output files from a single tool or a pipeline do not need to be
  # defined by the user.  If there is a required input or output file and it does not have its value set, 
  # determine how to construct the filename and populate the node with the value.
  gknoConfig.constructFilenames(pipelineGraph, config)

  # Check that all required files and values have been set. All files and parameters that are listed as
  # required by the infividual tools should already have been checked, but if the pipeline has some
  # additional requirements, these may not yet have been checked.
  config.checkRequiredFiles(pipelineGraph)

  # Check that all files have a path set.
  gknoConfig.setFilePaths(pipelineGraph, config)

  # If flags are linked in a pipeline configuration file, but none of them were set on the command line,
  # the nodes will have no values. This will cause problems when generating the makefiles. Search all
  # option nodes looking for flags and set any unset nodes to 'unset'.
  config.searchForUnsetFlags(pipelineGraph)

  # Prior to filling in missing filenames, check that all of the supplied data is consistent with
  # expectations.  This includes ensuring that the inputted data types are correct (for example, if
  # an argument expects an integer, check that the values are integers), filename extensions are valid
  # and that multiple values aren't given to arguments that are only allowed a single value.
  gknoConfig.checkData(pipelineGraph, config)

  # Check that all of the supplied values for the gkno specific nodes are valid.
  gknoConfig.checkNodeValues(pipelineGraph, config)

  # Find the maximum number of datasets for each task.
  config.getNumberOfDataSets(pipelineGraph)

  # Identify file nodes that are streaming.
  config.identifyStreamingNodes(pipelineGraph)

  # If there are multiple runs, multiple make files are created, using only the values for individual
  # iterations.
  make.determineMakefileStructure(pipelineGraph, config, hasMultipleRuns)
  makeFilename = make.getFilename(runName)

  # Set the output path for use in the makefile generation.
  make.getOutputPath(pipelineGraph, config)

  for phaseID in make.makefileNames:
    for iteration, makefileName in enumerate(make.makefileNames[phaseID]):

      # If multiple runs are being performed, the iteration needs to be sent to the various following
      # routines in order to pick the files necessary for the particular makefile. Otherwise, all
      # iterations of data should be used in the makefile (there is either only one iteration or
      # internal loops are required in which case, all of the iterations are used in the same file).
      # Set the 'key' to the iteration or 'all' depending on the run type.
      if hasMultipleRuns: key = iteration + 1
      else: key = 'all'

      # Open the makefile.
      makefileHandle = make.openMakefile(makefileName)

      # Write header information to all of the makefiles.
      make.writeHeaderInformation(sourcePath, runName, makefileName, makefileHandle, phaseID, key)

      # Write out the executable paths for all of the tools being used in the makefile.
      make.writeExecutablePaths(pipelineGraph, config, makefileHandle, make.tasksInPhase[phaseID])

      # Detemine which files are dependencies, outputs and intermediate files. Begin by marking all
      # intermediate file nodes. If a file node has both a predecessor and a successor, it is an
      # intermediate file. Mark the file node as such unless the pipeline configuration file specifically
      # states that the file should be kept.
      graphDependencies  = config.determineGraphDependencies(pipelineGraph, make.tasksInPhase[phaseID], key = key)
      graphOutputs       = config.determineGraphOutputs(pipelineGraph, make.tasksInPhase[phaseID], key = key)
      graphIntermediates = config.determineGraphIntermediateFiles(pipelineGraph, make.tasksInPhase[phaseID], key = key)

      # Write the intermediate files to the makefile.
      make.writeIntermediateFiles(makefileHandle, graphIntermediates)

      # Write the pipeline outputs to the makefile.
      make.writeOutputFiles(makefileHandle, graphOutputs)

      # Determine the task in which each intermediate file is last used. This will allow the files to
      # be deleted as early as possible in the pipeline.
      deleteList = config.setWhenToDeleteFiles(pipelineGraph, graphIntermediates)

      # Search through the tasks in the workflow and check for tasks outputting to a stream. Generate a
      # list of tasks for generating the makefiles. Each entry in the list should be a list of all tasks
      # that are piped together (in a pipeline with no streaming, this list will just be the workflow).
      taskList = make.determineStreamingTaskList(pipelineGraph, config, make.tasksInPhase[phaseID])

      # Write out the information for running each task.
      make.writeTasks(pipelineGraph, config, makefileName, makefileHandle, taskList, deleteList, key)

      # Close the makefile in preparation for execution.
      make.closeMakefile(makefileHandle)

      # Check that all of the input files exist.
      gknoConfig.checkFilesExist(pipelineGraph, config, graphDependencies, sourcePath)

  # If there are files required for the makefiles to run and theu don't exist, write a warning to the
  # screen and ensure that the makefiles aren't executed.
  gknoConfig.writeMissingFiles(pipelineGraph, config)

  # Check that all of the executable files exist.
  # checkExecutables()

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-DNL', 'values')[1][0] == 'unset':
    if isVerbose: write.writeTracking(phoneHomeID)
    phoneHome(sourcePath, phoneHomeID)
    if isVerbose: write.writeDone()
  write.writeBlankLine()

  # Execute the generated script unless the execute flag has been unset.
  success = 0
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-EXECUTE', 'values')[1][0]:
    for phaseID in make.makefileNames:
      for iteration, makefileName in enumerate(make.makefileNames[phaseID]):

        # Check if the '--number-jobs' option is set.  If so, request this number of jobs.
        numberOfJobs = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-JOBS', 'values')[1][0]
        execute      = 'make -j ' + str(numberOfJobs) + ' --file ' + makefileName
        if isVerbose: write.writeExecuting(execute)
        success = subprocess.call(execute.split())
        if isVerbose: write.writeComplete(success)

  # If the makefile was succesfully run, finish gkno with the exit condition of 0.
  # If the makefile failed to run, finish with the exit condition 3.  A failure
  # prior to execution of the makefile uses the exit condition 2.
  if success == 0: exit(0)
  else: exit(3)

if __name__ == "__main__":
  main()
