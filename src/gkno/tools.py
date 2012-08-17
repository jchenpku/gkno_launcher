#!/usr/bin/python

from __future__ import print_function
import os
import sys

import errors
from errors import *

class tools:

  # Initialise the tools class.
  def __init__(self):
    self.dependencies          = {}
    self.originalToolArguments = {}
    self.outputs               = {}
    self.tool                  = ''
    self.toolInfo              = {}
    self.toolArguments         = {}

  # If gkno is being run in the single tool mode, check that the specified tool
  # exists.
  def checkTool(self, gknoHelp):
    if self.tool not in self.toolInfo:
      gknoHelp.toolHelp    = True
      gknoHelp.printHelp   = True
      gknoHelp.unknownTool = True

  # For all of the tools, parse through the configuration files and ensure that all
  # necessary fields are present.  Later subroutines will assume they are, so
  # terminate here if the configuration file is incomplete.
  def checkForRequiredFields(self):
    er         = errors()
    firstError = True

    for task in self.toolInfo:
      for argument in self.toolInfo[task]['arguments']:

        # Check that the 'input' field is present...
        value = self.toolInfo[task]['arguments'][argument]['input'] if 'input' in self.toolInfo[task]['arguments'][argument] else ''
        if (value != 'true') and (value != 'false'):  er.missingFieldForTool('', task, argument, 'input', value)

        # output...
        value = self.toolInfo[task]['arguments'][argument]['output'] if 'output' in self.toolInfo[task]['arguments'][argument] else ''
        if (value != 'true') and (value != 'false'): er.missingFieldForTool('', task, argument, 'output', value)

        # required...
        value = self.toolInfo[task]['arguments'][argument]['required'] if 'required' in self.toolInfo[task]['arguments'][argument] else ''
        if (value != 'true') and (value != 'false'): er.missingFieldForTool('', task, argument, 'required', value)

        # dependent...
        value = self.toolInfo[task]['arguments'][argument]['dependent'] if 'dependent' in self.toolInfo[task]['arguments'][argument] else ''
        if (value != 'true') and (value != 'false'): er.missingFieldForTool('', task, argument, 'dependent', value)

        # type...
        value = self.toolInfo[task]['arguments'][argument]['type'] if 'type' in self.toolInfo[task]['arguments'][argument] else ''
        if (value != 'string') and (value != 'flag') and (value != 'integer') and (value != 'float'): 
          er.missingFieldForTool('', task, argument, 'type', value)

        # If the resource field is missing, assume that it isn't a resource file.
        value = self.toolInfo[task]['arguments'][argument]['resource'] if 'resource' in self.toolInfo[task]['arguments'][argument] else ''
        if value == '': self.toolInfo[task]['arguments'][argument]['resource'] == 'false'

    if er.error: er.terminate()

  # Loop over each tool in the pipeline and set up a hash of hashes.
  # For each tool, the set of allowed options along with default values
  # if defined.
  def setupToolOptions(self, cl, pl):
    er = errors()

    if self.toolArguments['pipeline']['--verbose']:
      print("Setting up tool defaults...", file = sys.stdout)
      sys.stdout.flush()
    for task in pl.information['workflow']:

      # Check if this tool name has already been used.  It is required that 
      # the names describing the order of the tools in the pipeline are unique.
      # This ensures that all tools can be anambiguously linked with any of the
      # others.
      if task in self.toolArguments:
        er.repeatedTool(task)
        er.terminate()

      # Parse new tools.
      else:
        tool = pl.information['tools'][task]
        if self.toolArguments['pipeline']['--verbose']:
          print("\t", tool, " (", task, ")...", sep = '', end = '', file = sys.stdout)
          sys.stdout.flush()
        self.toolArguments[task] = {}
        for argument in self.toolInfo[tool]['arguments']:

          # If a default value for the argument is assigned, set this value in the data structure.
          default = self.toolInfo[tool]['arguments'][argument]['default'] if 'default' in self.toolInfo[tool]['arguments'][argument] else ''

          # Determined the required data type.
          if 'type' not in self.toolInfo[tool]['arguments'][argument]:
            er.toolArgumentsError('type', tool, argument)
            er.terminate()

          # Check if a value for this particular option is required.
          if 'required' not in self.toolInfo[tool]['arguments'][argument]:
            er.toolArgumentsError('required', tool, argument)
            er.terminate()
          self.toolArguments[task][argument] = default
        if self.toolArguments['pipeline']['--verbose']:
          print("done.", file = sys.stdout)
          sys.stdout.flush()
    if self.toolArguments['pipeline']['--verbose']:
      print(file = sys.stdout)
      sys.stdout.flush()

  # Set up tl.originalToolArguments structure.
  def setupOriginalToolArguments(self):
    for task in self.toolArguments:
      if task not in self.originalToolArguments: self.originalToolArguments[task] = {}
      for argument in self.toolArguments[task]:
        if argument not in self.originalToolArguments[task]: self.originalToolArguments[task][argument] = {}
        self.originalToolArguments[task][argument] = self.toolArguments[task][argument]

  # Reset the tl.toolArguments structure.
  def resetDataStructures(self, pl):
    self.toolArguments = {}
    for task in self.originalToolArguments:
      if task not in self.toolArguments: self.toolArguments[task] = {}
      for argument in self.originalToolArguments[task]:
        if argument not in self.toolArguments[task]: self.toolArguments[task][argument] = {}
        self.toolArguments[task][argument] = self.originalToolArguments[task][argument]

    # Also reset the toolInfo structure.  If tools were streamed together, some
    # additional options have been added to toolInfo, but the added options were
    # tracked in the pl.addedToToolInfo structure.
    for task in pl.addedToToolInfo:
      for argument in pl.addedToToolInfo[task]: del(self.toolInfo[task]['arguments'][argument])

    # Reset other data structures.
    self.dependencies  = {}
    self.outputs       = {}
    pl.deleteFiles     = {}
    pl.finalOutputs    = {}
    pl.streamedOutputs = {}
    pl.taskBlocks      = []

  # For each tool, find the output files.  If these haven't already been given a
  # value, then a value needs to be assigned.  First check if there is a 'construct
  # filenames' block in the json file with instructions on how to build the filename
  # (this applies to pipelines only).  If there are no explicit instructions, check
  # if any of the input files have 'use for filenames' set to true.  If so, use this
  # filename to build the output (changing the extension as required).
  def constructFilenames(self, pl, task, tool):
    er = errors()

    if self.toolArguments['pipeline']['--verbose']:
      print("\t\tConstructing filenames...", end = '', file = sys.stdout)
      sys.stdout.flush()

    # First identify the input and output files and how their names should be constructed.
    filenameConstructor = ''
    inputFiles          = []
    outputFiles         = {}
    for argument in self.toolInfo[tool]['arguments']:
      isInput  = True if self.toolInfo[tool]['arguments'][argument]['input'] == 'true' else False
      isOutput = True if self.toolInfo[tool]['arguments'][argument]['output'] == 'true' else False

      # If this is an input file, check to see if it is to be used for building filenames.
      if isInput:
        inputFiles.append(argument)
        if 'use for filenames' in self.toolInfo[tool]['arguments'][argument]:
          if self.toolInfo[tool]['arguments'][argument]['use for filenames'] == 'true':

            # If there was an input file previous designated as the file to use for
            # constructing output filenames for this tool, gkno cannot determine which
            # file to use and so terminates.
            if filenameConstructor != '':
              er.multipleFilenameConstructors("\n\t\t", task, tool, argument, filenameConstructor)
              er.terminate()
            else:
              filenameConstructor = argument

      # If the argument is an output, check to see if it has already been defined.  If
      # not, store this as a filename to be constructed.
      if isOutput:
        if self.toolArguments[task][argument] == '':

          # For pipelines, check if the 'construct filenames' block exists and describes
          # how to build this filename.
          if pl.isPipeline and ('construct filenames' in pl.information):
            for constructTask in pl.information['construct filenames']:
              if constructTask == task:
                for constructArgument in pl.information['construct filenames'][constructTask]:
                  if constructArgument == argument: outputFiles[argument] = 'construct'
                  break

          if argument not in outputFiles: outputFiles[argument] = 'from input'

    # Now all of the output files have been identified and the method of filename generation
    # determined, build the filenames.
    for outputFile in outputFiles:

      # If to be constructed using information from the json file (pipelines), construct.
      if outputFiles[outputFile] == 'construct':
        pl.constructFileNameFromJson(self, task, tool, outputFile)

      elif outputFiles[outputFile] == 'from input':
        if filenameConstructor != '':
          self.constructFilenameFromInput(task, tool, outputFile, filenameConstructor)

        # If the output filename is to be generated using an input file from this task and there
        # are no input files designated as to be used for generating the filename, check what
        # input files there are.  If there is only one input for this task, use this file to
        # generate the filenames.  If there are no or multiple input files, terminate.
        else:
          if len(inputFiles) == 1:
            self.constructFilenameFromInput(task, tool, outputFile, inputFiles[0])
          else:
            er.unknownFilenameConstructor(True, "\t\t", task, tool, outputFile)
            er.terminate()
    if self.toolArguments['pipeline']['--verbose']:
      print('done.', file = sys.stdout)
      sys.stdout.flush()

  # If the output filename is to be constructed from an input filename, take the
  # requested input filename, remove the extension and replace with the required
  # extension for this output file.
  def constructFilenameFromInput(self, task, tool, outputFile, argument):
    er        = errors()
    inputFile = self.toolArguments[task][argument].split('/')[-1]

    # Check if the input file that is to be used for constructing the output filename is
    # blank.  If soi, terminate gkno as the output filename cannot be determined.
    if inputFile == '':
      er.noInputFilenameForFilenameConstruction(True, "\t\t\t", task, tool, outputFile, argument)
      er.terminate()
    else:
      inputExtension = ''
      for extension in self.toolInfo[tool]['arguments'][argument]['extension'].split('|'):
        if inputFile.endswith(extension):
          inputExtension = extension
          break

      # Strip off the extension.
      if inputExtension != '': inputFile = inputFile[0:(len(inputFile) - len(extension) - 1)]

      # Add the output extension unless the output is a stub.
      isStub = False
      if 'stub' in self.toolInfo[tool]['arguments'][outputFile]:
        if self.toolInfo[tool]['arguments'][outputFile]['stub'] == 'true': isStub = True
      if not isStub: self.toolArguments[task][outputFile] = inputFile + '.' + self.toolInfo[tool]['arguments'][outputFile]['extension'].split('|')[0]
      else: self.toolArguments[task][outputFile] = inputFile

  # Determine which files are required for each tool to run.  For each tool, these files
  # are stored in a list and are used to define the dependencies in the Makefile.
  def determineDependencies(self, cl, pl):
    er = errors()

    if self.toolArguments['pipeline']['--verbose']:
      print('Determine tool dependencies...', file = sys.stdout)
      sys.stdout.flush()
    for task in pl.information['workflow']:
      tool = pl.information['tools'][task]
      if self.toolArguments['pipeline']['--verbose']:
        print("\t", task, '...', sep = '', end = '', file = sys.stdout)
        sys.stdout.flush()

      self.dependencies[task] = []
      self.outputs[task]      = []

      for argument in self.toolArguments[task]:
        if argument == 'json parameters':
          value = self.toolArguments[task][argument]
          self.dependencies[task].append(value)
        else:

          # Check if the file is an input or an output file, or is listed as a dependent
          # file.  If it is an output, the file should be added to the string containing
          # all outputs from this tool.  If it is an input or dependent file, this will
          # be added to the string containing all files required for this tool to run.
          isInput     = True if self.toolInfo[tool]['arguments'][argument]['input'] == 'true' else False
          isOutput    = True if self.toolInfo[tool]['arguments'][argument]['output'] == 'true' else False
          isResource  = True if self.toolInfo[tool]['arguments'][argument]['dependent'] == 'true' else False
          isDependent = True if self.toolInfo[tool]['arguments'][argument]['resource'] == 'true' else False
          isFlag      = True if self.toolInfo[tool]['arguments'][argument]['type'] == 'flag' else False
  
          if isInput or isDependent or isOutput or isResource:
  
            # If the input/output file is defined, check that the extension is as expected.
            value = self.toolArguments[task][argument] if self.toolArguments[task][argument] != '' else ''
  
            # If this file needs to be added to one of the string, check to see if it is a stub
            # or not.  If so, all of the files associated with the stub need to be added to the
            # string.
            isStub = False
            if 'stub' in self.toolInfo[tool]['arguments'][argument]:
              if self.toolInfo[tool]['arguments'][argument]['stub'] == 'true': isStub = True
  
            # If this is a stub, create the string containing all of the files.
            if isStub:
  
              # If the file that the tool requires for successful execution is a stub,
              # make sure that all of the required files are listed in the list of
              # dependencies.
              if 'outputs' not in self.toolInfo[tool]['arguments'][argument]:
                print(file = sys.stdout)
                sys.stdout.flush()
                er.stubNoOutputs(tool, argument)
                er.terminate()
              else:
                for name in self.toolInfo[tool]['arguments'][argument]['outputs']:
                  if isOutput: self.outputs[task].append(value + name)
                  else: self.dependencies[task].append(value + name)
  
            # If the filename is not a stub, just include the value.
            else:
              if (value != '') and not isFlag:
                if isOutput: self.outputs[task].append(value)
                else: self.dependencies[task].append(value)

      if self.toolArguments['pipeline']['--verbose']:
        print("done.", file = sys.stdout)
        sys.stdout.flush()
    if self.toolArguments['pipeline']['--verbose']:
      print(file = sys.stdout)
      sys.stdout.flush()

  # Determine additional dependencies that are not associated with an input
  # command line argument.
  #
  # All of the included output files have already been added to the outputs
  # string for each tool if they appear on the command line.  There are some
  # programs that generate output files, however, without specifying the output
  # file.  In these instances, the additional output files for the tool are
  # included at the beginning of the tools configuration files.  Parse these
  # additional output files (if there are any) and add to the outputs string.
  def determineAdditionalFiles(self, pl):
    er = errors()
    if self.toolArguments['pipeline']['--verbose']:
      print('Determining additional dependencies and output files...', file = sys.stdout)
      sys.stdout.flush()

    # Loop over each tool in turn and check for additional output files.
    for task in pl.information['workflow']:
      if task not in self.outputs: self.outputs[task] = []
      tool = pl.information['tools'][task]
      if self.toolArguments['pipeline']['--verbose']:
        print("\t", task, " (", tool, ")...", sep = '', end = '', file = sys.stdout)
        sys.stdout.flush()
      if 'additional files' in self.toolInfo[tool]:

        # There are different formats for building up output files.  Each of these can
        # be dealt with separately.
        #
        # 1. If the output file can be constructed from a value given to one of the
        # tools command line arguments.
        if 'from input arguments' in self.toolInfo[tool]['additional files']:
          for argument in self.toolInfo[tool]['additional files']['from input arguments']:

            # Check that the command which should be used to determine the file name exists
            # and has a value defined.
            fileType = ''
            command  = ''
            filename = ''
            try: fileType = argument['type']
            except: er.error = True
            if er.error:
              print(file = sys.stdout)
              sys.stdout.flush()
              er.optionAssociationError('type', 'additional files\' -> \'from input arguments', task)
              er.terminate()

            try: command = argument['command']
            except: er.error = True
            if er.error:
              print(file = sys.stdout)
              sys.stdout.flush()
              er.optionAssociationError('command', 'additional files\' -> \'from input arguments', task)
              er.terminate()

            try: filename = self.toolArguments[task][command]
            except: er.error = True
            if er.error:
              print(file = sys.stdout)
              sys.stdout.flush()
              er.missingCommand(task, tool, command)
              er.terminate()
              
            # In constructing the output file name, the extension associated with the associated
            # file name can be stripped off and a new extension can be appended if requested.
            # Determine and enact the appropriate steps.
            if 'remove extension' in argument:
              if argument['remove extension'] == 'true':
                filename = filename.rpartition('.')[0]
            if 'add extension' in argument:
              if argument['add extension'] == 'true':
                try: extension = argument['output extension']
                except: er.error = True
                if er.error:
                  print(file = sys.stdout)
                  sys.stdout.flush()
                  er.optionAssociationError('output extension', 'additional files\' -> \'from input arguments', task)
                  er.terminate()
                filename += '.' + extension

            # If the file is a dependency, add to the dependency string, otherwise add to the
            # output string.
            if fileType == 'dependency': self.dependencies[task].append(filename)
            elif fileType == 'output': self.outputs[task].append(filename)
            else:
              er.unknownDependencyOrOutput(task, fileType)
              er.terminate()

      if self.toolArguments['pipeline']['--verbose']:
        print("done.", file = sys.stdout)
        sys.stdout.flush()
    if self.toolArguments['pipeline']['--verbose']:
      print(file = sys.stdout)
      sys.stdout.flush()
