#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import version2.pipelineConfiguration as pipelineConfiguration
import version2.toolConfiguration as toolConfiguration
import version2.pipelineConfigurationErrors as perr

import json
import os
import sys

# Define a class to store task attributes.
class superpipelineClass:
  def __init__(self, pipeline):

    # Define errors.
    self.pipelineErrors = perr.pipelineErrors()

    # Record the name of the top level pipeline, e.g. that defined on the command line.
    self.pipeline = None

    # The number of tiers in the super pipeline.
    self.numberOfTiers = 1

    # Store all of the pipeline configuration files comprising the superpipeline in a
    # dictionary, indexed by the name of the pipeline.
    self.pipelineConfigurationData = {}

    # Store information on all the constituent tools.
    self.toolConfigurationData = {}

    # Store all the tasks in the superpipeline along with the tools,
    self.tools = []
    self.tasks = {}

    # Store the unique and shared node IDs in all the pipeline.
    self.uniqueNodeIDs = []
    self.sharedNodeIDs = []

    # Store all of the constituent pipeline with their tier and also all the pipelines indexed
    # by tier.
    self.pipelinesByTier = {}
    self.tiersByPipeline = {}

    # Keep track of the tasks that should be included in a plot.
    self.tasksInPlot = {}

  # Starting from the defined pipeline, process and validate the configuration file contents,
  # then dig down through all the nested pipelines and validate their configuration files.
  def getNestedPipelineData(self, path, filename):

    # Get the top level pipeline configuration file data.
    pipeline = pipelineConfiguration.pipelineConfiguration()
    pipeline.getConfigurationData(filename)
    self.pipelineConfigurationData[pipeline.name] = pipeline

    # Store the name of the tier 1 pipeline (e.g. the pipeline selected on the command line).
    self.tiersByPipeline[pipeline.name] = 1
    self.pipelinesByTier[1]             = [pipeline.name]
    self.pipeline                       = pipeline.name

    # Now dig into the nested pipeline and build up the super pipeline structure.
    tier = 2
    checkForNestedPipelines = True
    while checkForNestedPipelines:
      tierHasNestedPipeline = False
      for currentPipelineName in self.pipelinesByTier[tier - 1]:
        currentPipeline = self.pipelineConfigurationData[currentPipelineName]
  
        # If the pipeline contains a pipeline as a task, process the configuration file for that
        # pipeline and add to the pipelines in the current tier.
        if currentPipeline.hasPipelineAsTask:
          tierHasNestedPipeline = True
          for taskPointingToNestedPipeline, nestedPipeline in currentPipeline.requiredPipelines:
            filename = path + str(nestedPipeline) + '.json'
            pipeline = pipelineConfiguration.pipelineConfiguration()
            pipeline.getConfigurationData(filename)
  
            # Construct the address of the task.
            pipeline.address = '' if currentPipeline.address == None else str(currentPipeline.address) + '.'
            pipeline.address += str(taskPointingToNestedPipeline)
            self.pipelineConfigurationData[pipeline.address] = pipeline

            # Store the pipeline name with the tier it's on.
            if tier not in self.pipelinesByTier: self.pipelinesByTier[tier] = []
            self.pipelinesByTier[tier].append(pipeline.address)
            self.tiersByPipeline[pipeline.address] = tier

        # Increment the tier. If no pipelines in the just processed tier had a nested pipeline, the
        # loop can end.
        tier += 1
        if not tierHasNestedPipeline: checkForNestedPipelines = False
  
  # Check that none of the pipeline arguments conflict with gkno arguments.
  def checkForArgumentConflicts(self, longForms, shortForms):
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]:
        for longFormArgument in self.pipelineConfigurationData[pipeline].longFormArguments:
          shortFormArgument = self.pipelineConfigurationData[pipeline].longFormArguments[longFormArgument].shortFormArgument
          if longFormArgument in longForms: self.pipelineErrors.conflictWithGknoArguments(longFormArgument, shortFormArgument, isLongForm = True)
          if shortFormArgument in shortForms: self.pipelineErrors.conflictWithGknoArguments(longFormArgument, shortFormArgument, isLongForm = False)

  # Get all of the tools from each pipeline in the super pipeline and store them.
  def setTools(self):
    for tier in self.pipelinesByTier:
      for pipelineName in self.pipelinesByTier[tier]:
        pipeline = self.pipelineConfigurationData[pipelineName]

        # Loop over all of the pipeline tasks.
        for task in pipeline.getAllTasks():

          # Get the pipeline relative address of the task.
          taskAddress = str(pipeline.address + '.' + task) if pipeline.address else str(task)

          # Get the tool for the task.
          tool = pipeline.getTaskAttribute(task, 'tool')

          # If this tool is not yet in the tools list, include it.
          if tool not in self.tools: self.tools.append(tool)

          # Store the task with its tool.
          self.tasks[taskAddress] = tool

          # Store whether the task should be included in a plot.
          self.tasksInPlot[taskAddress] = not pipeline.getTaskAttribute(task, 'omitFromReducedPlot')

        # Store the unique and shared node IDs for each pipeline.
        self.uniqueNodeIDs += [str(pipeline.address + '.' + nodeID) if pipeline.address else str(nodeID) for nodeID in pipeline.getUniqueNodeIDs()]
        self.sharedNodeIDs += [str(pipeline.address + '.' + nodeID) if pipeline.address else str(nodeID) for nodeID in pipeline.getSharedNodeIDs()]

  # Check that all references to tasks in the pipeline configuration file are valid. The task may
  # be a task in a contained pipeline and not within the pipeline being checked. The allTasks
  # list contains all of the tasks in all of the pipelines.
  def checkContainedTasks(self):

    # Loop over all the tiers in the super pipeline.
    for tier in self.pipelinesByTier:
      for pipelineName in self.pipelinesByTier[tier]:
        pipelineObject = self.pipelineConfigurationData[pipelineName]

        # Check the tasks that any unique nodes point to.
        for nodeID in pipelineObject.uniqueNodeAttributes.keys():
    
          # Get the name of the task that this node points to. This is the full address of the
          # task and so may live in a nested pipeline.
          task = pipelineObject.getUniqueNodeAttribute(nodeID, 'task')
    
          # This pipeline may itself be called by an enveloping pipeline. If so, any tasks
          # will require prepending with the address of this pipeline.
          if pipelineObject.address: task = pipelineObject.address + '.' + task
    
          # If the task is not listed as one of the pipeline tasks. terminate.
          if task not in self.tasks: pipelineObject.errors.invalidTaskInNode(pipelineName, 'unique', nodeID, task, self.tasks)
    
        # Check the tasks that shared nodes point to.
        for sharedNodeID in pipelineObject.sharedNodeAttributes.keys():
          for node in pipelineObject.sharedNodeAttributes[sharedNodeID].sharedNodeTasks:
            task           = pipelineObject.getNodeTaskAttribute(node, 'task')
            taskArgument   = pipelineObject.getNodeTaskAttribute(node, 'taskArgument')
            externalNodeID = pipelineObject.getNodeTaskAttribute(node, 'externalNodeID')

            # Add the address of the current pipeline if this is not the top tier pipeline.
            if pipelineObject.address: task = pipelineObject.address + '.' + task

            # If the externalNode is set, the node is in an external pipeline and is being pointed
            # to directly. Ensure that the task argument is not also defined and then construct the
            # name of the graph node to test for existence.
            if externalNodeID:
              if taskArgument: print('superpipeline.checkContainedTasks - 2'); exit(0)
              task = task + '.' + externalNodeID
              if task not in self.uniqueNodeIDs and task not in self.sharedNodeIDs:
                pipelineObject.errors.invalidTaskInNode(pipelineName, 'shared', sharedNodeID, task, self.tasks)

            # If the node defines a task and a task argument (not a node, as above), check that the task
            # exists. This task could be in another pipeline.
            else:
              if task not in self.tasks: pipelineObject.errors.invalidTaskInNode(pipelineName, 'shared', sharedNodeID, task, self.tasks)

  # Given a pipeline name and a node ID, return the node type (i.e. unique or shared).
  def getNodeType(self, pipeline, nodeID):

    # Define the node address.
    address = pipeline + '.' + nodeID
    if address in self.uniqueNodeIDs: return 'unique'
    elif address in self.sharedNodeIDs: return 'shared'
    else: return None

  # Add tool configuration data to the super pipeline.
  def addTool(self, tool, toolData):
    self.toolConfigurationData[tool] = toolData

  # Check that all tool arguments reference in pipeline configuration files are valid.
  def checkArgumentsInPipeline(self):
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]: 

        # Get a list of all the tool arguments contained in each pipeline.
        arguments = self.pipelineConfigurationData[pipeline].getToolArguments()

        # Check that each argument is valid.
        for nodeType, nodeID, task, argument in arguments:

          # Get the tool associated with the task.
          address     = self.pipelineConfigurationData[pipeline].address + '.' if self.pipelineConfigurationData[pipeline].address else ''
          taskAddress = str(address + task)
          tool        = self.tasks[taskAddress]

          # Get the long form of the supplied argument.
          longFormArgument = self.toolConfigurationData[tool].getLongFormArgument(argument)

          # If the long form does not exist, the argument in the pipeline configuration file is not valid.
          if not longFormArgument:
            self.pipelineConfigurationData[pipeline].errors.invalidToolArgument(pipeline, nodeType, nodeID, task, tool, argument)

  # Return the tool used for a task. The task is the full address, so may well be a task
  # buried within enclosed pipelines.
  def getTool(self, taskAddress):

    # Consider a task from a tier two pipeline. This would have an address of the form,
    # 'pipeline.task'. The tier one pipeline would just have the name of the task in the pipeline.
    namesList    = taskAddress.split('.')
    task         = namesList.pop()
    pipelineName = '.'.join(namesList) if namesList else self.pipeline

    # Get the pipeline configuration data for this pipeline.
    try: return self.pipelineConfigurationData[pipelineName].getTaskAttribute(task, 'tool')
    except: return False

  # Determine which nodes are intermediate (e.g. are listed in the shared nodes section of the
  # pipeline configuration file with the 'delete files' set).
  def determineFilesToDelete(self, graph):

    # Loop over all pipelines in the superpipeline.
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]:

        # Loop over all of the shared nodes.
        for nodeID in self.pipelineConfigurationData[pipeline].getSharedNodeIDs():
          if self.pipelineConfigurationData[pipeline].getSharedNodeAttribute(nodeID, 'isDelete'):
            address     = self.pipelineConfigurationData[pipeline].address
            nodeAddress = str(address + '.' + nodeID) if address else str(nodeID)
            for graphNodeID in graph.configurationFileToGraphNodeID[nodeAddress]: graph.setGraphNodeAttribute(graphNodeID, 'isIntermediate', True)

  #######################################################
  ## Methods to get information from the superpipeline ##
  #######################################################

  # Return all the tools used in the superpipeline.
  def getTools(self):
    return self.tools

  # Return data for a specified tool.
  def getToolData(self, tool):
    try: return self.toolConfigurationData[tool]
    except: return False

  # Get a parameter set for a tool.
  def getToolParameterSet(self, tool, parameterSet):
    try: return self.toolConfigurationData[tool].parameterSets.sets[parameterSet]
    except: return None

  # Get a tool argument attribute.
  def getToolArgumentAttribute(self, tool, argument, attribute):
    try: return self.toolConfigurationData[tool].getArgumentAttribute(argument, attribute)
    except: return False

  # Return all the arguments for a tool.
  def getToolArguments(self, tool):
    return self.toolConfigurationData[tool].arguments

  # Return pipeline data.
  def getPipelineData(self, pipeline):
    try: return self.pipelineConfigurationData[pipeline]
    except: return False

  # Get a parameter set for a pipeline.
  def getPipelineParameterSet(self, pipeline, parameterSet):
    try: return self.pipelineConfigurationData[pipeline].parameterSets.sets[parameterSet]
    except: return None

  # Get a node attribute.
  def getNodeAttribute(self, nodeID, attribute):

    # Consider a task from a tier two pipeline. This would have an address of the form,
    # 'pipeline.task'. The tier one pipeline would just have the name of the task in the pipeline.
    namesList    = nodeID.split('.')
    nestedNodeID = namesList.pop()
    pipelineName = '.'.join(namesList) if namesList else self.pipeline
    nodeType     = self.getNodeType(pipelineName, nestedNodeID)

    # If this is a unique node, get the attribute.
    if nodeType == 'unique':
      try: return self.pipelineConfigurationData[pipelineName].getUniqueNodeAttribute(nestedNodeID, 'description')
      except: return False

    # If this is a shared node, get the attribute.
    if nodeType == 'shared':
      try: return self.pipelineConfigurationData[pipelineName].getSharedNodeAttribute(nestedNodeID, 'description')
      except: return False
