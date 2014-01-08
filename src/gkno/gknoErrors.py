#!/usr/bin/python

from __future__ import print_function
import os
import sys

class gknoErrors:

  # Initialise.
  def __init__(self):
    self.hasError  = False
    self.text      = []

  # Format the error message and write to screen.
  def writeFormattedText(self, errorType):
      firstLine = True
      secondLine = False
      maxLength = 93 - 5
      print(file = sys.stderr)
      for line in self.text:
        textList = []
        while len(line) > maxLength:
          index = line.rfind(' ', 0, maxLength)
          if index == -1:
            index = line.find(' ', 0, len(line))
            if index == -1:
              textList.append(line)
              line = ''
            else:
              textList.append(line[0:index])
              line = line[index + 1:len(line)]
          else:
            textList.append(line[0:index])
            line = line[index + 1:len(line)]

        if line != '' and line != ' ': textList.append(line)
        line = textList.pop(0)
        while line.startswith(' '): line = line[1:]

        if firstLine and errorType == 'error':
          print('ERROR:   %-*s' % (1, line), file=sys.stderr)
        elif firstLine and errorType == 'warning':
          print('WARNING: %-*s' % (1, line), file=sys.stderr)
        elif secondLine:
          print('DETAILS: %-*s' % (1, line), file=sys.stderr)
          secondLine = False
        else:
          print('         %-*s' % (1, line), file=sys.stderr)
        for line in textList:
          while line.startswith(' '): line = line[1:]

          if secondLine: print('DETAILS: %-*s' % (1, line), file=sys.stderr)
          else: print('         %-*s' % (1, line), file=sys.stderr)

        if firstLine:
          print(file=sys.stderr)
          firstLine = False
          secondLine = True

  ##################
  # Terminate gkno #
  ##################
  def terminate(self):
    print(file=sys.stderr)
    print('================================================================================================', file=sys.stderr)
    print('  TERMINATED: Errors found in running gkno.  See specific error messages above for resolution.', file=sys.stderr)
    print('================================================================================================', file=sys.stderr)
    exit(2)

  #####################################
  # Error with pipeline construction. #
  #####################################

  # The pipeline contains an isolated node.
  def isolatedNodes(self, graph, config, isolatedNodes):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Isolated node in pipeline.')
    self.text.append('The following nodes do not share any files with any other task in the pipeline. This may be by design, but is often ' + \
    'a sign that the pipeline configuration file is not complete.')
    self.text.append('\t')
    for nodeID in isolatedNodes: self.text.append('\t' + nodeID)
    self.text.append('\t')
    self.writeFormattedText(errorType = 'warning')

  #################################
  # Errors with the command line. #
  #################################

  # A required pipeline argument is missing.
  def missingPipelineArgument(self, graph, config, argument, shortForm, description):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('The required command line argument ' + argument + ' (' + shortForm + ') is missing.')
    self.text.append('This argument is described as the following: ' + description)
    self.text.append('\t')
    self.text.append('Check the usage information for all required arguments.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # A required argument is missing.
  def missingArgument(self, graph, config, task, argument, shortForm, description):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('A required command line argument is missing.')
    self.text.append('The task \'' + task + '\' requires the argument \'' + argument + ' (' + shortForm + ')\' to be set, but it has ' + \
    'not been specified on the command line. This argument cannot be set using a pipeline argument and consequently must be set using the syntax:')
    self.text.append('\t')
    self.text.append('./gkno pipe <pipeline name> --' + task + ' [' + argument + ' <value>] [options]')
    self.text.append('\t')
    self.text.append('This argument is described as the following: ' + description)
    self.text.append('\t')
    self.text.append('It is recommended that the pipeline configuration file be modified to ensure that all arguments required by the pipeline ' + \
    'have a command line argument defined in the pipeline configuration file. Please see the documentation for further information on how this ' + \
    'can be accomplished.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # A file extension is invalid.
  def invalidExtension(self, filename, extensions, longForm, shortForm, task, argument, shortFormArgument):
    self.text.append('Incorrect extension on file: ' + filename)

    # If this file can be set with a pipeline argument, indicate the values.
    if longForm != None:
      self.text.append('The file defined for argument \'' + longForm + ' (' + shortForm + ')\' must take one of the following extensions:')

    # If this file is associated with an argument set directly to the tool using the syntax:
    # 'gkno pipe <pipeline name> --task [argument value]', indicate the task and argument and
    # the allowed extensions.
    else:
      self.text.append('The file defined for task \'' + task + '\', argument \'' + argument + ' (' + shortFormArgument + ')\' must take one \
of the following extensions:')

    # List the allowed extensions and write the error message.
    for counter, extension in enumerate(extensions): self.text.append('\t' + str(counter + 1) + ': ' + extension)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # Invalid data type.
  def invalidDataType(self, graph, config, longFormArgument, shortFormArgument, description, value, expectedDataType):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('A command line argument was given an invalid value.')
    self.text.append('The command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' was given the value \'' + value + \
    '\'. This value is invalid. The expected data type for this argument is \'' + expectedDataType + '\'. This argument is described as: ' + \
    description)
    self.text.append('\t')
    self.text.append('Please provide a valid value for this argument.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ######################################################
  # Errors with required files/directories/executables #
  ######################################################

  # If input files are missing, warn the user, but don't terminate gkno.
  def missingFiles(self, graph, config, files):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    tool = 'tool' if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'tool' else 'pipeline'
    self.text = ['Required files are missing.']
    self.text.append('The following files are required for this ' + tool + ' to run:')
    self.text.append('\t')
    for filename in files: self.text.append('\t' + filename)
    self.writeFormattedText(errorType = 'warning')

  # If input files are missing, warn the user, but don't terminate gkno.
  def missingOutputDirectory(self, graph, config, directory):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text = ['Output directory does not exist.']
    self.text.append('The output directory was defined as \'' + directory + '\'. This directory does not exist. Please check that the specified \
directory is correct, or create prior to execution of gkno. Automatic execution has been disabled.')
    self.writeFormattedText(errorType = 'warning')

  #######################################
  # Errors with constructing filenames. #
  #######################################

  # A argument required for building a filename is missing.
  def missingArgumentInFilenameConstruction(self, graph, config, argument):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text = ['An argument required for constructing a filename is missing.']
    self.text.append('gkno is attempting to the generate a filename using instructions from the tool configuration file. An argument required \
to do this is missing, however. Please ensure that the argument \'' + argument + '\' is set.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()
  
  # As above, except, for the specific case where gkno is running in pipeline mode and the required argument is
  # not a pipeline argument.
  def missingArgumentInFilenameConstructionNotPipelineArgument(self, graph, config, task, argument):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text = ['An argument required for constructing a filename is missing.']
    self.text.append('gkno is attempting to generate a filename using instructions from the tool configuration file. An argument required \
to do this is missing. The required argument is \'' + argument + '\' for task \'' + task + '\' and there is no pipeline argument that sets this \
value. The value can be set using the syntax \'--' + task + ' [' + argument + ' <value>]\', however it would be preferable if a pipeline \
argument existed to set this value. Please see the documentation to see how to include this in the pipeline configuration file.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()
  




































  #############
  # File errors
  #############

  # If a requested file is missing, terminate.
  def missingFile(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing configuration file.'
    self.text.append(text)
    text = "The file '" + filename + "' could not be located."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the requested json file cannot be succesfully read into a data structure, terminate citing
  # the errors generated by the Python json handler.
  def jsonOpenError(self, newLine, error, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed json file: ' + filename
    self.text.append(text)
    text = str(error) + '.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ################################
  # Tool configuration file errors
  ################################

  # If the tool configuration file is missing the dictionary heading tools, terminate.
  def missingToolsBlockInConfig(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The configuration file does not contain a 'tools' block. This block contains " + 'all the information for a tool and must be ' + \
    'present.  Please check the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a field is defined in the configuration file, that gkno does not understand, terminate.
  def undefinedFieldInConfig(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    if ',' in field: field = field.replace(',', ' -> ')
    text = "The configuration file contains the field '" + field + "' for tool '" + tool + "'.  This field is not a valid entry for the " + \
    'configuration file.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a field is required by gkno and it does not appear in the configuration file, terminate.
  def missingRequiredFieldInConfig(self, newLine, filename, tool, missingVariables):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The following required variables for tool '" + tool + "' are missing from the configuration file:"
    self.text.append(text)
    for field in missingVariables:
      if ',' in field: field = field.replace(',', ' -> ')
      self.text.append('\t' + field)

    self.writeFormattedText()
    self.hasError = True

  # If the data type in the config file is different to that expected (as defined by the same
  # config file), terminate.
  def differentDataTypeInConfig(self, newLine, filename, tool, field, given, defined):
    if ',' in field: field = field.replace(',', ' -> ')
    if given == int: givenString = 'integer'
    elif given == float: givenString = 'float'
    elif given == bool: givenString = 'boolean'
    elif given == str: givenString = 'string'
    elif given == list: givenString = 'list'
    elif given == dict: givenString = 'dictionary'
    elif given == tuple: givenString = 'tuple'
    else: givenString = 'unknown'

    if defined == int: definedString = 'integer'
    elif defined == float: definedString = 'float'
    elif defined == bool: definedString = 'boolean'
    elif defined == str: definedString = 'string'
    elif defined == list: definedString = 'list'
    elif defined == dict: definedString = 'dictionary'
    elif defined == tuple: definedString = 'tuple'
    else: definedString = 'unknown'

    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = 'The data type (' + givenString + ") for field '" + field + "' "
    if tool != '': text += "in tool '" + tool + "' "
    text += 'is inconsistent with that expected (' + definedString + ').  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument appears in the argument order list that is not an argument associated with the
  # tool, terminate.
  def unknownArgumentInArgumentOrder(self, newLine, filename, tool, argument):
      if newLine: print(file=sys.stderr)
      text = 'Malformed configuration file: ' + filename
      self.text.append(text)
      text = "The configuration file for tool '" + tool + "' contains a list defining the order in which the arguments are to be written.  " + \
      'An unknown argument (' + argument + ') is present in this list.  Please check the configuration file and remove/repair invalid fields.'
      self.text.append(text)
      self.writeFormattedText()
      self.hasError = True

  # The argument order must contain a complete list of all arguments for the specified tool.  If
  # any arguments are missing from this list, terminate.
  def argumentMissingFromArgumentOrder(self, newLine, filename, tool, argument):
      if newLine: print(file=sys.stderr)
      text = 'Malformed configuration file: ' + filename
      self.text.append(text)
      text = "The configuration file for tool '" + tool + "' contains a list defining the order in which the arguments are to be written.  " + \
      'This list must contain all of the arguments defined for this tool, but the argument \'' + argument + "' is missing.  Please check " + \
      'the configuration file and remove/repair invalid fields.'
      self.text.append(text)
      self.writeFormattedText()
      self.hasError = True

  # If the argument is to be replaced in the event of the input being a stream, the field "replace
  # argument with" must be present.  If it is not, terminate.
  def replaceArgumentMissing(self, newLine, filename, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The configuration file for tool '" + tool + "' contains the argument '" + argument + "'.  This argument contains the field " + \
    '\'"if argument is stream" : "replace"\'.  This field instructs gkno that if the input to the tool is a stream, the command line argument ' + \
    'needs to be replaced by a different string.  The field "replace argument with" must, therefore, also be present.  This field is a ' + \
    'dictionary telling gkno what to replace the argument and value with, but is missing for this argument. Please check the configuration ' + \
    'file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument is being replaced (in the event of an input stream), the "replace argument with" dictionary must
  # include both an "argument" and "value".  If either of these fields are missing, terminate.
  def missingFieldInReplace(self, newLine, filename, tool, argument, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The field '" + argument + "' in tool '" + tool + '\' needs to be a dictionary containing two fields: "argument" and "value".  ' + \
    "The field '" + field + "' is missing.  Please check the configuration file and remove/repair invalid fields."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a tool is outputtng a stub, a list of output files must also be included.  If these are missing, teminate.
  def missingOutputsForStub(self, newLine, filename, tool, argument, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' for tool '" + tool + '\' has the "stub" field set to true.  This means that the argument defines ' + \
    'an output stub.  In this case, there must also be a list of the filenames that will be produced by this tool.  These are defined using ' + \
    'the "outputs" field for this argument.  This is not present in this case.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the field 'list of input files' is associated with a tool, it must also include the 'apply by repeating
  # this argument' field.  Terminate if this is missing.
  def missingArgumentToRepeat(self, newLine, filename, tool, argument, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' for tool '" + tool + '\' has the "list of input files" field set to true.  This means that the ' + \
    "argument defines a file containing a list of input files.  In this case, there must also be reference to the command line argument " + \
    'which will accept these files as input.  This is defined using the "apply by repeating this argument" field for this argument.  This ' + \
    'is not present in this case.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the argument listed in 'apply by repeating this argument' is not an argument associated with this tool, 
  # terminate.
  def invalidArgumentInRepeat(self, newLine, filename, tool, argument, text, value):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' for tool '" + tool + '\' contains the "apply by repeating this argument" field.  This field should ' + \
    "be accompanied by an argument associated with this tool.  The included value (" + value + ") is not a recognised command line argument " + \
    "for this tool.  Please check the configuration file and remove/repair invalid fields."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a Boolean was expected in the configuration file, but some other data type is present, terminate.
  def incorrectBooleanValue(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Command line error with argument: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The argument '" + a + "' expects a Boolean as input.  gkno will accept the values: 'true', 'True', 'false' or 'False'.  " + \
      "The value '" + value + "' is not accepted.  Please check and " + 'modify the command line.'
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Missing value for argument: ' + argument
      self.text.append(text)
      text = "The argument '" + argument + "' was specified for task '" + task + "' and it expects a Boolean as input.  gkno will accept the " + \
      "values: 'true', 'True', 'false' or 'False'.  The value '" + value + "' is not accepted.  " + 'Please check and modify the command line.'
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a Boolean was expected in the configuration file, but some other data type is present, terminate.
  def incorrectDefaultBooleanValue(self, newLine, task, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Default parameter error for argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The argument '" + argument + "' was specified for task '" + task + "' and it expects a Boolean as input.  gkno will accept the " + \
    "values: 'true', 'True', 'false' or 'False'.  The value '" + value + "' is not accepted.  " + 'Please check and modify the command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  def incorrectDefaultDataType(self, newLine, task, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect default data type for command line argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The command line argument '" + argument + "' was specified for task '" + task + "' and it expects a value of type '" + dataType + \
    "'.  The given value (" + value + ') is not of this type.  Please check and rectify the given command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unknown field appears in the 'additional files' section, terminate.
  def unknownFieldInAdditionalFiles(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field \'' + field + '\'.  This is not an allowed value.  ' + \
    'Please check and rectify the given command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unknown field appears in the 'additional files' section, terminate.
  def unknownFieldInAdditionalFilesDictionary(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  This is a list of dictionaries, ' + \
    'and one of these contains the unknown field \'' + field + '\'.  This is not an allowed value.  Please check and rectify the tool ' + \
    'configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the tyoe field does not have a valid value, terminate.
  def typeInAdditionalFieldsError(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  One of the dictionaries ' + \
    'within this has the field "type" set to \'' + field + '\'.  This field can only take the values "output" or "dependency".  Plase check ' + \
    'repair the toool configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a required field in the additional files section is missing, terminate.
  def missingFieldInAdditionalFiles(self, newLine, filename, tool, missingField, required):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  The following fields must ' + \
    'appear for each of the dictionaries in the list:'
    self.text.append(text)
    self.text.append('\t')
    for field in required: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'The field \'' + missingField + '\' is missing.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the additional files has a set of defined filenames included, the type (output or dependency)
  # needs to be provided, but isn't.
  def missingTypeDefinedFilenamesInAdditionalFiles(self, newLine, filename, tool, missingField):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "defined filenames".  The following fields must ' + \
    'appear within this section:'
    self.text.append(text)
    self.text.append('\t')
    text = 'type: takes the value \'dependency\' or \'output\', depending on the nature of the additional files.'
    self.text.append(text)
    text = 'file list: the list of filenames to include as either dependencies or outputs.'
    self.text.append(text)
    self.text.append('\t')
    text = 'The field \'' + missingField + '\' is missing.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the additional files has a set of defined filenames included, the type (output or dependency)
  # needs to be provided.  If this does not take the value 'output' or 'dependency', terminate.
  def unknownTypeDefinedFilenamesInAdditionalFiles(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown value in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "defined filenames".  Within this section, there is a ' + \
    'list of filenames and the field "type".  The "type" field defines whether the additional files are dependencies for the tool or outputs ' + \
    'generated by the tool.  This must take the value "dependency" or "output".  The given value is: ' + field + '. Please check and repair the ' + \
    'configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "link to thie argument" field in the "additional files" section contains an unknown
  # argument, terminate.
  def unknownArgumentInAdditionalFiles(self, newLine, filename, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unknown argument in "additional files" in configuration file: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  The "link to this argument" ' + \
    'field must be a valid argument for this tool.  The argument \'' + argument + '\' is unknown.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "remove extension" field in the "additional files" section is not a Boolean, terminate.
  def incorrectBooleanInAdditionalFiles(self, newLine, filename, tool, field, value):
    if newLine: print(file=sys.stderr)
    text = 'Invalid Boolean in "additional files" section of configuration file: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' expects a Boolean value for the field \'' + field + '\'.  The given value \'' + \
    value + '\' is not a Boolean and is thus invalid.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ####################################
  # Pipeline configuration file errors
  ####################################

  # The pipeline workflow must consist of a set of ordered, uniquely named tasks.  The workflow
  # for the pipeline in question contains at least one non-uniquely named task.
  def multipleTasksWithSameName(self, newLine, task, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The pipeline workflow is an ordered list of tasks to perform.  Each of the tasks must be uniquely named, however, the task '" + task + \
    "' appears multiple times.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unrecognised section appears in the pipeline configuration file, terminate.
  def unknownSectionsInPipelineConfig(self, newLine, sections, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The configuration file contains the following sections that are unrecognised by gkno:'
    self.text.append(text)
    for section in sections: self.text.append("\t'" + section + "'")
    self.text.append('\t')
    text = 'Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a dictionary was expected, but a different type obesrved, terminate.
  def pipelineSectionIsNotADictionary(self, newLine, sectionName, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The '" + sectionName + "' section in the configuration file is not a dictionary of key/value pairs as required.  Please check " + \
    'and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a list was expected, but a different type obesrved, terminate.
  def pipelineSectionIsNotAList(self, newLine, sectionName, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The section '" + sectionName + "' in the configuration file is not a list as required.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a task was observed that is not part of the workflow, terminate.
  def taskNotInWorkflow(self, newLine, sectionName, task, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The '" + sectionName + "' section in the configuration file contains a task (" + task + ') that is not in the pipeline workflow. ' + \
    'Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline section is missing, terminate.
  def missingPipelineSection(self, newLine, sectionName, additionalText, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The configuration file does not contain the required '" + sectionName + "' section.  " + additionalText + '  Please check and ' + \
    'repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a task in the pipeline is associated with a tool with no configuration file of its own, terminate.
  def taskAssociatedWithNonExistentTool(self, newLine, task, tool, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The 'tools' in the configuration file contains a task (" + task + ') that is associated with a tool (' + tool + ') that is not ' + \
    'available in the gkno package.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline argument is missing a description, terminate.
  def pipelineArgumentMissingDescription(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required description field. " + \
    "Please include a description of this argument for other users who may use this pipeline."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline argument is missing the expected data type, terminate.
  def pipelineArgumentMissingType(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required description of the  " + \
    "data type.  Please include this \"type\" field for this argument in the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline argument is missing a short form, terminate.
  def pipelineArgumentMissingShortForm(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required short form.  All " + \
    "arguments are required to have a long form (--long-form) and a short form (-sf), for example.  Please include a short form value for this " + \
    "argument in the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If information from the arguments section is missing, terminate.
  def pipelineArgumentMissingInformation(self, newLine, argument, missingField, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required field '" + \
    missingField + "'.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument links to a task not in the workflow, terminate.
  def invalidLinkedTaskInArguments(self, newLine, task, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The configuration file contains information for a task that is not present in the pipeline workflow (\'' + task + '\').  Please ' + \
    'check the configuration file and ensure that all pipeline arguments are for allowed tasks.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument linked to an unknown argument, terminate.
  def invalidArgumentInConstruct(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\' contains the argument \'' + argument + '\' which is not a vaild ' + \
    'argument for this task.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the construct filenames section contains an unknown field, terminate.
  def unknownFieldInConstruct(self, newLine, task, argument, field, allowedFields, filename):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised field in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the field \'' + field + \
    '\'.  The only fields allowed for the arguments in the "construct filenames" section are:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowedFields: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If any of the required fields in the construct filenames section are missing, terminate.
  def missingFieldInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has certain required fields.  The task \'' + \
    task + '\', argument \'' + argument + '\' is missing the field \'' + field + '\'.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'additional text from parameters' field appears in construct filenames, check that it is a dictionary. If
  # not, terminate.
  def additionalTextInConstructNotADict(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has the field "additional text from parameters" included.  This ' + \
    'field must be a dictionary, but is not.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'additional text from parameters' field appears in construct filenames and the order field is missing,
  # terminate.
  def orderMissingInAdditionalTextInConstruct(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has certain required fields.  The task \'' + \
    task + '\', argument \'' + argument + '\' contains the "additional arguments from parameters" field.  When this field is present, a list ' + \
    'titled "order" must be present describing the order in which to include these parameters into the new filename.  Please check and repair ' + \
    'the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'additional text from parameters' field appears in construct filenames, and the order field is not a list, terminate.
  def additionalTextOrderInConstructNotAList(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has the field "additional text from parameters" included.  The "order" ' + \
    'section within this should be a list of the additional pieces of text that will appear in the constructed filename.  This list must contain ' + \
    'all of the fields defined in the "additional text from parameters" section.  The "order" field is not a list in this configuration file.  ' + \
    'Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a name appearing in the "order" for the "additional text from parameters" is not defined with a link to a task
  # and argument, terminate.
  def missingTextDefinitionInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains the field \'' + field + '\' in the "order" section in ' + \
    'task \'' + task + '\', argument \'' + argument + '\', but this isn\'t defined.  Each name appearing in the "order" - with the exception ' + \
    ' of "filename root" - needs to be defined with a link to a task and argument.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If required information is missing defining which argument to use in constructing a filename, terminate.
  def missingRootInformationInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section "filename root" field is set to "from argument" for task \'' + task + \
    '\', argument \'' + argument + '\'.  In this case, it is necessary that the "get root from task" and "get root from argument" fields are ' + \
    'also defined.  However, the field "' + field + '" is missing.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root" field is "from argument" and the "remove input extension" field is not a Boolean, terminate.
  def invalidRootDataTypeInConstruct(self, newLine, task, argument, value, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the field "remove input ' + \
    'extension" field.  This field is required to be a Boolean, but the given value (' + value  + ') is not. Please check and repair the ' + \
    'pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root" field is "from argument" and the linked argument is invalid, terminate.
  def invalidRootArgumentInConstruct(self, newLine, task, argument, givenArgument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the field "get root from ' + \
    'argument" field.  This is set to \'' + givenArgument + '\' which is not vaild for the tool.  Please check and repair the pipeline ' + \
    'configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root text" field is missing when 'filename root' is set to 'from text', terminate.
  def filenameRootTextMissing(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing value in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' has the "filename root" field set to \'' + \
    'from text\'.  When this is set, the field \'filename root text\' must also be present with a string to be used as the root of the ' + \
    'filename.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root" field is set to an invalid value, terminate.
  def unknownRootValue(self, newLine, task, argument, field, allowed, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid value in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' has the "filename root" field set to \'' + \
    field + '\'.  This is not an allowed value for this field.  This field can take one of the following values:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowed: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If required information is missing defining which argument to use in constructing a filename, terminate.
  def missingFieldInTextDefinitionInConstruct(self, newLine, task, argument, field, additionalText, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains a definition for \'' + field + '\' for task \'' + task + \
    '\', argument \'' + argument + '\' in the "additional text from parameters" section.  This definition is missing the required field \'' + \
    additionalText + '\'.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a defined argument for use in constructing a filename is not recognised, terminate.
  def invalidArgumentInConstructAdditional(self, newLine, task, argument, field, linkedTask, linkedArgument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains the "additional text from parameters" section for task \'' + \
    task + '\', argument \'' + argument + '\'.  The defined parameter \'' + field + '\' is linked to the argument \'' + linkedArgument + \
    '\', but this argument is not recognised for the linked task \'' + linkedTask + '\'.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a parameter is defined in the additional text section of the configuration file and it doesn't
  # appear in the "order" list, terminate.
  def definedTextNotInOrderInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains the "additional text from parameters" section for task \'' + \
    task + '\', argument \'' + argument + '\'.  The defined parameter \'' + field + '\' does not appear in the "order" list and so cannot ' + \
    'be used in the filename construction. Please check the configuration file and ensure that all defined parameters appear in the "order" list.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the additional text field value for "remove extension" is not a Boolean, terminate.
  def invalidAdditionalDataTypeInConstruct(self, newLine, task, argument, additionalSection, value, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the "additional text from ' + \
    'parameters" field.  Within this, the section titled \'' + additionalSection + '\' contains the field "remove extension".  This field is ' + \
    'required to be a Boolean, but the given value (' + value  + ') is not. Please check and repair the ' + \
    'pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an expected field is missingin the linkage section, terminate.
  def missingFieldInLinkage(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The field \'' + field + '\' is required ' + \
    'within this section, but is missing.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument not associated with the task, terminate.
  def invalidArgumentInLinkage(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\' contains the argument \'' + argument + '\' which is not associated with the ' + \
    'task.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an unknown field, terminate.
  def unknownFieldInLinkage(self, newLine, task, argument, field, allowedFields, filename):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised field in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' contains the field \'' + field + '\'.  The only ' + \
    'fields allowed for the arguments in the linkage section are:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowedFields: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument linked to an unknown task, terminate.
  def invalidLinkedTask(self, newLine, task, argument, linkedTask, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid linked task in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' links to the task \'' + linkedTask + '\', which is ' + \
    'not in the pipeline workflow.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument linked to an unknown argument, terminate.
  def invalidLinkedArgument(self, newLine, task, argument, linkedTask, linkedArgument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid linked argument in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' links to the task \'' + linkedTask + '\', argument \'' + \
    linkedArgument + '\'.  This is not a valid argument for this task.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains a list for the linkedTask or linkedArgument field and the
  # associated linkedTask/linkedArgument is not a list, fail.
  def linkedTaskArgumentIsNotAList(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Inconsistent lists in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' contains a list for either the linked task or the ' + \
    'linked argument, but not both.  The \'link to this task\' and the \'link to this argument\' sections can be a list, but if either is, then ' + \
    'both must be.  The linked task list would contain the tasks from which to link an argument and the linked argument list would be the ' + \
    'arguments from each of the tasks (in the same order).  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unknown field appears in the "delete files" section, terminate.
  def unknownFieldInDeleteFiles(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The field \'' + field + \
    '\' is included for this argument, but this field is not valid.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the delete files section contains an invalid argument, terminate.
  def unknownArgumentInDeleteFiles(self, newLine, task, tool, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  This task uses the tool \'' + \
    tool + '\' and this argument is not valid for this tool.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'output extension' list is included in the 'delete files' section and it is not
  # a list, terminate.
  def outputExtensionNotAListInDeleteFiles(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "output extension" field ' + \
    'is present for this argument, but it is not a list as expected.  The "output extension" list is used when the argument produces multiple ' + \
    'output files and so the specific files to be deleted are indicated with this list.  The "delete after task" field for this argument must ' + \
    'also be a list, indicating the task after which each file in the "output extension" list should be deleted.   Please check and repair ' + \
    'the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'delete after task' field is missing, terminate.
  def deleteAfterTaskMissing(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "delete after task" field ' + \
    'must be included for all arguments, but is missing here.  If the "output extension field is present, the "delete after task" field must ' + \
    'be a list with the same number of entries, otherwise, it is the task after whose successful operation the file should be deleted.  Please ' + \
    'check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'delete after task' field is not a list when the "output extension" field is also present, terminate.
  def deleteAfterTaskNotAList(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "delete after task" field ' + \
    'must be a list for this argument, since the "output extension" list was also included.  This list should include the task after which the ' + \
    'file should be deleted, for each of the file extensions included in the "output extension" list (in the same order).  ' + \
    'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'delete after task' list is not the same size as the 'output extension' list, terminate.
  def listsDifferentSizeInDeleteFiles(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "delete after task" field ' + \
    'and the "output extension" lists are both included, but have different lengths.  For each extension in the "output extensions" list, there ' + \
    'must be a corresponding entry in the "delete after files" list describing which task to delete that particular file after.  Please check ' + \
    'and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the extension for the file to delete is not a valid extension for the tool, terminate.
  def invalidExtensionInDeleteFiles(self, newLine, task, argument, extension, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The extension of the file ' + \
    'being deleted is set as \'' + extension + '\' but this is not the extension associated with outputs from this task.  Please check ' + \
    'and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #####################
  # Command line errors
  #####################

  # An unknown argument appears on the command line.
  def unknownArgument(self, newLine, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unknown command line argument: ' + argument
    self.text.append(text)
    text = "The argument '" + argument + "' is not associated with the tool or pipeline being executed.  Please check and repair the command line."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If commands for a specific tool are included, but the square brackets enclosing the arguments
  # are not terminated. fail.
  def unterminatedTaskSpecificOptions(self, newLine, task):
    if newLine: print(file=sys.stderr)
    text = 'Arguments for specific task are incomplete: ' + task
    self.text.append(text)
    text = 'Arguments for task \'' + task  + '\' are provided.  Arguments for a specific task must be enclosed in square brackets, but these ' + \
    'were not terminated.  Please check and amend the command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ######################
  # Multiple runs errors
  ######################

  # If ths file containing the multiple runs data can't be found, terminate.
  def noMultipleRunFile(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'File not found: ' + filename
    self.text.append(text)
    text = "Multiple runs were requested with the --multiple-runs (-mr) command and the file '" + filename + "' was provided as the file " + \
    'containing the necessary information.  This file could not be found.  Please check the command line and the location of the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument appears in the multiple runs format list that is not an argument associated with the
  # tool, terminate.
  def unknownArgumentInMultipleRuns(self, newLine, filename, argument):
    if newLine: print(file=sys.stderr)
    text = 'Malformed multiple runs file: ' + filename
    self.text.append(text)
    text = 'The multiple runs file contains a list defining the command line arguments that will be modified in each run.  An unknown argument (' + \
    argument + ') is present in this list.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a flag was given an invalid value in an instance, terminate.
  def flagGivenInvalidValueMultiple(self, newLine, filename, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised flag in multiple runs file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += "', in the multiple runs file expects flags as input.  gkno will accept the values: 'true', 'True', 'false' or 'False'.  " + \
    "The value '" + value + "' is not accepted.  Please check the multiple runs file and rectify any errors in the data or order of the data."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the multiple runs file contains unexpected information for a Boolean value, terminate.
  def incorrectBooleanValueInMultiple(self, newLine, filename, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect data type for in multiple runs file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += "', in the multiple runs file expects Boolean values as input.  gkno will accept the values: 'true', 'True', 'false' or 'False'.  " + \
    "The value '" + value + "' is not accepted.  Please check the multiple runs file and rectify any errors in the data or order of the data."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a data type in the multiple runs file is not as expected, terminate.
  def incorrectDataTypeInMultiple(self, newLine, filename, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect data type for in multiple runs file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += "', set in the multiple runs file expects a value of type '" + dataType + "'.  The given value (" + value + ') is not of this type.  ' + \
    'Please check the multiple runs file and rectify any errors in the data or order of the data.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # The data list must contain a multiple of the number of entries in the format of data list section.
  # gkno will read the expected format and then for each run, read the values for each value specified
  # in this list.  If there isn't an integral multiple, the values for each run are not given correctly,
  # so terminate.
  def incorrectNumberOfEntriesInMultipleJson(self, newLine, setID, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed multiple runs input file: ' + filename
    self.text.append(text)
    text = 'The number of entries in the "values" section must be a multiple of the number of entries in the "arguments".  For each ' + \
    'makefile generated, the command line arguments defined in the "arguments" will be set with a value taken from the "values" ' + \
    'section.  This means that the "values" section is an ordered list of each argument in the format list repeated for the number ' + \
    'of runs required.  Please ensure that the multiple runs file is correctly built.'
    self.text.append(text)
    self.text.append('\t')
    text = 'The data set at fault is that with ID: ' + setID
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # A required section is missing from the multiple runs file.
  def missingSectionMultipleRunsFile(self, newLine, filename, section):
    if newLine: print(file=sys.stderr)
    text = 'Malformed multiple runs input file: ' + filename
    self.text.append(text)
    text = 'The multiple-runs input file must contain two sections.  The first section is titled "arguments" and is a list ' + \
    'of the command line arguments for which data appears in the second section.  The second section is titled "values" and contains ' + \
    "the data.  The provided file is missing the '" + section + "' section.  Please check and repair the multiple runs file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #################
  # Instance errors
  #################

  # The requested information doesn't exist.
  def noInstanceInformation(self, newLine, path, name, instance):
    if newLine: print(file=sys.stderr)
    text = 'No information for requested instance: ' + instance
    self.text.append(text)
    text = 'Instance information cannot be found.  An instance of the given name must be present in the configuration file (' + path + name + \
    '.json) or in the separate instance file (' + name + '_instances.json) in the same directory.  The requested instance (' + instance + \
    ') is not present in either of these files.  If the instance is being created, modify the external instances file to contain this instance.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # Each instance must include a description.
  def noInstanceDescription(self, newLine, instance, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The instance '" + instance + "' does not contain a description as required.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # Only one instance can be selected to avoid conflict between set parameters.
  def multipleInstances(self, newLine):
    if newLine: print(file=sys.stderr)
    text = 'Multiple instances requested.'
    self.text.append(text)
    text = 'Instances can be used to set certain parameters for the tool/pipeline.  Only one instance can be requested, however.  Multiple ' + \
    'instances have been requested on the command line.  Please check the command line for repetition of the --instance (-is) command and ' + \
    'ensure that it appears only once (or not at all).'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the instance information for a Boolean value is not as expected, terminate.
  def incorrectBooleanValueInInstance(self, newLine, name, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Error with argument (from instance): ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The argument '" + argument + "', set as part of the instance '" + name + "', expects a Boolean as input.  gkno will accept " + \
    "the values: 'true', 'True', 'false' or 'False'.  The value '" + value + "' is not accepted.  Please check the instance " + \
    'information in the configuration file (or instance file) and rectify any errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the data type in the instance is not as expected, terminate.
  def incorrectDataTypeInInstance(self, newLine, name, task, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect data type for command line argument (in instance): ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The command line argument '" + argument + "', set as part of the instance '" + name + "', was specified for task '" + task + \
    "' and it expects a value of type '" + dataType + "'.  The given value (" + value + ') is not of this type.  Please check and rectify ' + \
    'the given command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a flag was given an invalid value in an instance, terminate.
  def flagGivenInvalidValueInstance(self, newLine, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised flag for (instance) argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = 'If a flag argument is included in an instance, the value supplied with it must be either "set" or "unset" to instruct gkno ' + \
    "whether to include the argument on the command line or not.  The argument '" + argument + "' is a flag, but was supplied with the " + \
    "value '" + str(value) + "'.  Please check the entry for this argument in the instance section of the configuration file (or the separate " + \
    'instance configuration file).'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If there is an additional instances file and it contains no instance information, terminate.
  def instancesFileHasNoInstances(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with file: ' + filename
    self.text.append(text)
    text = 'The instances file \'' + filename + '\' should only contain information about instances for the tool/pipeline with which ' + \
    'it is associated.  This file does not contain the \'instances\' block required.  Please check this instances file for errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an instance description in an additional instance file has the same name as an instance in the
  # configuration file, terminate.
  def instanceNameAlreadyExists(self, newLine, instance, filename):
    if newLine: print(file=sys.stderr)
    text = 'Multiple instance definitions with name: ' + instance
    self.text.append(text)
    text = 'The instances file \'' + filename + '\' contains an instance with the name \'' + instance + '\', however, an instance of this ' + \
    'name is already present in the configuration file.  Please ensure that all of the instances defined for a specific tool/pipeline have ' + \
    'unique names (only modify entries in the instances file if possible).'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ###################################
  # Errors with exporting an instance
  ###################################

  # If the user is attempting to export an instance and they have supplied a file for performing multiple
  # runs, terminate.
  def exportInstanceForMultipleRuns(self, newLine):
    if newLine: print(file=sys.stderr)
    text = 'Error in attempting to export instance file.'
    self.text.append(text)
    text = 'An instance can only be exported if gkno is being run without the --multiple-runs (-mr) command line argument.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the --export-instance argument includes additional information.  This should be a flag.
  def noInstanceNameInExport(self, newLine, value, filename):
    if newLine: print(file=sys.stderr)
    text = 'No instance name provided for exporting an instance.'
    self.text.append(text)
    text = 'The --export-instance (-ei) command line argument requires the desired instance name to be provided.  The provided value (' + value + \
    ') is either not a string or is missing.  When outputting a new instance, the file \'' + filename + '\' will store the instance information ' + \
    'with the supplied name.  Please check the command line for errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the --export-instance argument requests an instance name that already exists, terminate.
  def instanceNameExists(self, newLine, name):
    if newLine: print(file=sys.stderr)
    text = 'Requested instance name already exists: ' + name
    self.text.append(text)
    text = 'The --export-instance (-ei) command line argument sets the name of the instance to be output.  The requested name \'' + name + \
    '\' is already defined, either in the configuration file or the instances file.  Please select a different name for the outputted instance.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # An unrecognised argument appears in the instance file.
  def unknownArgumentInInstance(self, newLine, name, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unknown command line argument (from instance): ' + argument
    self.text.append(text)
    text = "The argument '" + argument + "', present in the instance '" + name + "' is not associated with the tool or any tools in the " + \
    'pipeline (if a pipeline is being executed).  Please check the instance information in the configuration file and repair.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # The instance contains information that is invalid.  Specifically, a supplied command line argument
  # does not fit with the tool requested.
  def invalidArgumentInInstance(self, newLine, instance, argument):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in instance: ' + instance
    self.text.append(text)
    text = "The argument '" + argument + "' appears in the list of arguments for instance '" + instance + "' but this is not " + \
    'a valid argument for this tool/pipeline.  Please check the instance arguments in the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #################################
  # Errors with makefile generation
  #################################

  ##########################
  # Errors with dataChecking
  ##########################

  # If a file with multiple inputs contained can't be found, terminate.
  def noInputFileList(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'File not found: ' + str(filename)
    self.text.append(text)
    text = "An input file list was included, but the file '" + str(filename) + "' could not be found.  Please check the command line and the " + \
    'location of the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the file containindg the list of input files is malformed (e.g. doesn't have the "filename
  # list" field and the format of this field is not a list, terminate.
  def malformedFilenameList(self, newLine, filename, task, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Malformed file list in file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in task '" + task + "' defines a file containing a list of files that will be read in " + \
    'by the tool.  The format of the file is not recognised.  This file needs to be a json file with the key "filename list" defining a ' + \
    'list of files.  Please check and repair the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If multiple input files are designated as the filename constructor for constructing filenames, terminate
  # as gkno cannot determine which to use.
  def multipleFilenameConstructors(self, newLine, task, tool, argumentA, argumentB):
    if newLine: print(file=sys.stderr)
    text = 'Muliple files listed as filename constructors.'
    self.text.append(text)
    text = 'Multiple arguments for task \'' + task + '\' (tool: \'' + tool + '\') have the "use for filenames" field set to true.  If this ' + \
    'field is set to true, gkno will use this input file to construct other filenames, but if multiple arguments have this value set, gkno ' + \
    'cannot determine which argument to use.  The arguments \'' + argumentA + '\' and \'' + argumentB + '\' are both set to be used for ' + \
    'filename construction.  Please check and repair the configuration file for this tool.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an input filename is not defined and the tool configuration file indicates that the filename should not
  # be constructed according to rules in the pipeline configuration file, terminate as gkno requires a
  # filename.
  def missingFilenameNotToBeConstructed(self, newLine, task, tool, argument, shortForm, pipelineArgument, pipelineShortForm):
    if newLine: print(file=sys.stderr)
    text = 'Unable to construct missing filename.'
    self.text.append(text)
    text = 'A required filename is missing and cannot be constructed from other files as the "do not construct from input file" field has ' + \
    'been set in the tool configuration file.  The required file is for the task \'' + task + '\'.  This links to the tool \'' + tool + '\' and ' + \
    'the argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += '\' within this tool.'
    self.text.append(text)
    self.text.append('\t')
    text = 'Please set the pipeline command line argument \'' + pipelineArgument
    if pipelineShortForm != '': text += ' (' + pipelineShortForm + ')'
    text += '\' or check and modify the tool configuration file entry.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a filename is to be constructed, but no information was provided on how to construct it and the
  # task has multiple input files, gkno cannot determine which file to use for filename construction.
  # Terminate.
  def unknownFilenameConstructor(self, newLine, task, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unable to construct output filename.'
    self.text.append(text)
    text = 'The pipeline contains the task \'' + task + '\'.  This task uses the tool \'' + tool + '\'.  An output argument for this tool (' + \
    argument + ') needs a value, but was not set on the command line and has no instructions in the configuration file on how to construct ' + \
    'it.  This tool either has multiple inputs or the input file is also not specified, so gkno cannot construct the output file using the ' + \
    'input file as a template.'
    self.text.append(text)
    self.text.append('\t')
    text = 'Please make sure that all required arguments are set on the command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the extension for a file is not as expected, terminate.
  def fileExtensionError(self, newLine, task, argument, shortForm, link, filename, extension):
    if newLine: print(file=sys.stderr)
    text = 'Unexpected extension on file: ' + filename
    self.text.append(text)
    text = 'The file in question does not end with the expected extension \'' + extension + '\'.  This file is associated with task \'' + \
    task + '\', argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    if link != '':
      pipelineArgument  = link[0]
      pipelineShortForm = link[1]
      text += '\', which can be set directly on the command line using the pipeline argument \'' + pipelineArgument
      if pipelineShortForm != '': text += ' (' + pipelineShortForm + ')'
      text += '\'.'
    else: text += '\'.  '
    self.text.append(text)
    self.text.append('\t')
    text = 'Please check that all of the inputted files are correct.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a required field has not been set, terminate.
  def missingRequiredValue(self, newLine, task, argument, shortForm, isPipeline, pipelineArgument, pipelineShortForm):
    if newLine: print(file=sys.stderr)
    text = 'Required command line argument missing: '
    if pipelineArgument != '':
      text += pipelineArgument
      if pipelineShortForm != '': text += ' (' + pipelineShortForm + ').'
    else:
      text += argument
      if shortForm != '': text += ' (' + shortForm + ').'
    self.text.append(text)
    text = 'Argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += '\' for task \'' + task + '\' has not been set and is required for gkno to run.  '
    if pipelineArgument != '':
      text += 'This argument can be set from the command line with the pipeline argument \'' + pipelineArgument
      if pipelineShortForm != '': text += ' (' + pipelineShortForm + ')'
      text += '\'.  '
    text += 'Please set all required arguments for gkno to run.  For help with tool/pipeline operation, please use the --help argument for ' + \
    'extra information.'
    self.text.append(text)
    if isPipeline and pipelineArgument == '':
      self.text.append('\t')
      text = 'WARNING: This is a command for a tool internal to the pipeline and cannot be set directly on the command line.  It is likely ' + \
      'that this argument should be set using the linkage section of the configuration file.  Please check that this is the case.'
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # The given value for a parameter is of an unexpected type.
  def incorrectDataType(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Incorrect data type for command line argument: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The command line argument '" + a + "' expects a value of type '" + dataType + "'.  The given value (" + value + \
      ') is not of this type.  Please check and rectify the given command line.'
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Incorrect data type for command line argument: ' + argument
      if shortForm != '': text += ' (' + shortForm + ')'
      self.text.append(text)
      text = "The command line argument '" + argument + "' was specified for task '" + task + "' and it expects a value of type '" + dataType + \
      "'.  The given value (" + value + ') is not of this type.  Please check and rectify the given command line.'
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # A command line argument appears on the command line multiple times.  Each argument can only be
  # set once to avoid confilct between requested parameters.
  def multipleDefinitionsForSameArgument(self, newLine, task, argument, shortForm):
    if newLine: print(file=sys.stderr)
    text = 'Multiple definitions for command line argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The argument was specified multiple times for the task '" + task + "'.  In order to specify the same command line argument " + \
    'multiple times, the configuration file (for the associated tool) must contain \' "allow multiple definitions" : true\' in the definition ' + \
    'of the argument.  Please check the command line and if this argument should be allowed multiple definitions, ensure that the ' + \
    'corresponding configuration file reflects this.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # A flag is defined multiple times.
  def multipleDefinitionsForFlag(self, newLine, task, argument, shortForm):
    if newLine: print(file=sys.stderr)
    text = 'Multiple definitions for command line argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = 'The command line argument (' + argument + ") for task '" + task + "' is a flag.  This argument can only appear on the command " + \
    'line once, but it is defined multiple times.  Please check the command line for repetition of this flag.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # Non-flag arguments require a value to be set.
  def missingArgumentValue(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Missing value for argument: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The argument '" + a + "' expects a value of type '" + dataType + "', but no value was provided.  Please check the command line."
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Missing value for argument: ' + argument
      if shortForm != '': text += ' (' + shortForm + ')'
      self.text.append(text)
      text = "The argument '" + argument + "' was specified for task '" + task + "' and it expects a value of type '" + dataType + \
      "', but no value was provided.  Please check the command line."
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # Flags should not be accompanies be a value.
  def flagGivenValue(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Value given to flag: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The argument '" + a + "' is a flag and doesn't expect a value to be supplied.  The value '" + value + "' was provided on the " + \
      "command line.  Please check the given command line."
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Value given to flag: ' + argument
      if shortForm != '': text += ' (' + shortForm + ')'
      self.text.append(text)
      text = "The argument '" + argument + "' was specified for task '" + task + "'.  This argument is a flag and doesn't expect a value to " + \
      "be supplied.  The value '" + value + "' was provided on the command line.  Please check the given command line."
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a tool is instructed to accept a stream as input, but instructions are not included in the
  # configuration file, terminate.
  def noInputStreamInstructions(self, newLine, task, tool):
    if newLine: print(file=sys.stderr)
    text = 'Insufficient information for handling streaming tools.'
    self.text.append(text)
    text = 'The task \'' + task + '\' which uses the tool \'' + tool  + '\' accepts a stream as input as part of this pipeline.  However, ' + \
    'no instructions appear in the configuration file for this tool on how to deal with an input stream.  Please modify the tool configuration ' + \
    'file to allow accepting an input stream, or modify the pipeline configuration file to remove the streamed input.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a tool is instructed to output to stream, but instructions are not included in the
  # configuration file, terminate.
  def noOutputStreamInstructions(self, newLine, task, tool):
    if newLine: print(file=sys.stderr)
    text = 'Insufficient information for handling streaming tools.'
    self.text.append(text)
    text = 'The task \'' + task + '\' using tool \'' + tool + '\' is instructed to output to a stream, however, the configuration file for ' + \
    'this tool provides no instructions on outputting to a stream.  Please modify the tool configuration ' + \
    'file to allow accepting an input stream, or modify the pipeline configuration file to remove the streamed input.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If there are any missing executables, terminate.
  def missingExecutables(self, newLine, missingExecutableList):
    if newLine: print(file=sys.stderr)
    text = 'Missing executable files'
    self.text.append(text)
    text = 'The following executable files are not available, but are required:'
    self.text.append(text)
    self.text.append('\t')
    for executable in missingExecutableList: self.text.append(executable)
    self.writeFormattedText()
    self.hasError = True

  # If there is an unrecognised field in the 'additional dependencies' section, fail.
  def unrecognisedFieldInAdditionalDependencies(self, newLine, task, field, allowedFields, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The \'additional dependencies\' section contains dependency information for the task \'' + task + '\'.  An unrecognised field (' + \
    field + ') was included for this task.  The allowed fields for each task are:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowedFields: self.text.append(field)
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append('\t')
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the task output section in the additional dependencies points to an unknown task, fail.
  def unknownTaskInAdditionalDepedenciesTaskOutput(self, newLine, task, linkedTask, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The \'additional dependencies\' section contains information for task \'' + task + '\'.  Within the \'task output\' section, ' + \
    'the task \'' + linkedTask + '\' is listed as a task from which to get a dependency, but this is not a task in the pipeline workflow.  ' + \
    'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ######################
  # Internal loop errors
  ######################

  # If an internal loop file was specified on the command line, but the pipeline does not
  # have any internal loop information set up, terminate.
  def internalLoopRequestedButUndefined(self, newLine, pipelineName, filename):
    if newLine: print(file=sys.stderr)
    text = 'Attempt to use internal loop when none is defined: ' + filename
    self.text.append(text)
    text = 'The command line includes the \'--internal-loop\' argument, requesting that the pipeline loop over certain tasks in the ' + \
    'workflow.  This is only permissible for pipelines where information about internal loops has been provided in the configuration file. ' + \
    'The pipeline being run (' + pipelineName + ') does not have any information abomut an internal loop.  Please remove the internal loop ' + \
    'request from the command line, or modify the pipeline to accept internal loops.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unrecognised section appears in the file, terminate.
  def missingSectionsInternalLoop(self, newLine, section, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed internal loop file: ' + filename
    self.text.append(text)
    text = 'The file does not contain the required section \'' + section + '\'.  Please check and repair the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument in the internal loop file is for a task outside of the internal loop, fail.
  def argumentForTaskOutsideInternalLoop(self, newLine, argument, shortForm, linkedTask, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The \'arguments\' section of the file contains a list of arguments that are set in the \'values\' section.  These arguments must ' + \
    'link to tasks within the internal loop (see the pipeline configuration file for these tasks), but the argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += '\' links ' + \
    'to the task \'' + linkedTask + '\' which is not in the loop.  Please correct the internal loop file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument in the internal loop file is unknown, fail.
  def unknownArgumentInternalLoop(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The \'arguments\' section of the file contains a list of arguments that are set in the \'values\' section.  The argument \'' + \
    argument + '\' is unknown.  Please correct the internal loop file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If one of the blocks of values has a different number of values as arguments supplied, fail.
  def incorrectNumberOfValuesInInternalLoopFile(self, newLine, blockID, noValues, noArguments, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The \'values\' section of the file should be blocks of values, each with an ID.  There must be the same number of entries in each ' + \
    'of these blocks of values as there are arguments in the \'arguments\' section.  The block of values with ID \'' + str(blockID) + '\' has ' + \
    str(noValues) + ' entries, but ' + str(noArguments) + ' are expected.  Please check the internal loop file and fix any errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the data type is wrong, terminate.
  def incorrectDataTypeinInternalLoop(self, newLine, blockID, argument, value, dataType, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The value \'' + value + '\' appearing in the \'values\' section in block \'' + str(blockID) + '\' is associated with the argument \'' + \
    argument + '\'.  This argument expects a value of type \'' + dataType + '\' but the supplied value is not of this type.  Please check the ' + \
    'internal loop file and fix any errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If gkno is instructed to delete a file after a task in the internal loop, whcn the file
  # was the output of a task before the internal loop, there may be problems.  The tasks in
  # the internal loop may all require this file, so it shouldn't be deleted until after all
  # iterations are complete.
  def deleteFileInLoop(self, newLine, task, deleteAfterTask):
    if newLine: print(file=sys.stderr)
    text = 'Error with deleting files during pipeline operation.'
    self.text.append(text)
    text = 'The "delete files" section in the pipeline configuration file instructs gkno to delete files generated in task \'' + task + \
    '\' after execution of task \'' + deleteAfterTask + '\'.  gkno does not allow files to be deleted after a task included in an internal ' + \
    'loop unless the file to delete was generated by another task within the loop, which is not the case in this pipeline.  Please check and ' + \
    'modify the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #####################
  # Admin mode errors
  #####################
  
  def attemptingRemoveUnknownResource(self, resourceName, dest=sys.stderr):
    self.errorType = 'WARNING'
    print("WARNING: Resource '" + resourceName + "' was not removed because it is unknown", file=dest)

  def extractTarballFailed(self, filename, dest=sys.stderr):
    print("ERROR: Could not extract contents of"+filename, file=dest)

  def gitSubmoduleUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/submodule_update.* files for more details.", file=dest)

  def gitUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/gkno_update.* files for more details.", file=dest)

  def gknoAlreadyBuilt(self):
    print("Already built.", file=sys.stdout)

  def gknoNotBuilt(self, dest=sys.stderr):
    print("ERROR: 'gkno build' must be run before performing this operation", file=dest)

  def invalidResourceArgs(self, mode, dest=sys.stderr):
    print("ERROR: Invalid arguments or order used. Type 'gkno", mode, "--help' for a usage example.", file=dest)
    
  def noCurrentReleaseAvailable(self, resourceName, dest=sys.stderr):
    print("ERROR: Resource: " + resourceName + " has no release marked as 'current'. Cannot fetch.", file=dest)

  def noReleaseUrlFound(self, resourceName, releaseName, dest=sys.stderr):
    print("ERROR: Could not fetch files for resource: "+resourceName+", release: "+releaseName+" - URL not found", file=dest)

  def requestedUnknownResource(self, resourceName, dest=sys.stderr):
    print("ERROR: Requested resource '" + resourceName + "' is not recognized", file=dest)

  def resourceAlreadyAdded(self, resourceName, dest=sys.stderr):
    print("WARNING: Requested resource '" + resourceName + "' has already been added to gkno", file=dest)

  def resourceFetchFailed(self, resourceName, dest=sys.stderr):
    print("ERROR:  See logs/build_"+resourceName+".* files for more details.", file=dest)
  
  def toolBuildFailed(self, toolName, dest=sys.stderr):
    print("ERROR: See logs/build_"+toolName+".* files for more details.", file=dest)

  def toolUpdateFailed(self, toolName, dest=sys.stderr):
    print("ERROR: See logs/update_"+toolName+".* files for more details.", file=dest)

  def urlRetrieveFailed(self, url, dest=sys.stderr):
    print("ERROR: Could not retrieve file at "+url, file=dest)
    
  def dependencyCheckFailed(self, missing, unknown, incompatible, dest=sys.stderr):
    if len(missing) > 0:
      print("    Missing:", file=dest)
      for dep in missing:
        print("        ",dep.name, sep="", file=dest)
      print("", file=dest)
    if len(incompatible) > 0:
      print("    Not up-to-date:", file=dest)
      for dep in incompatible:
        print("        ", dep.name, 
              "    minimum version: ", dep.minimumVersion, 
              "    found version: "  , dep.currentVersion, sep="", file=dest)
      print("", file=dest)
    if len(missing) > 0 or len(incompatible) > 0:
      print("", file=dest)
      print("gkno (and its components) require a few 3rd-party utilities", file=dest)
      print("to either build or run properly.  To obtain/update the utilities ", file=dest)
      print("listed above, check your system's package manager or search the ", file=dest)
      print("web for download instructions.", file=dest)
      print("", file=dest)

    # ODD CASE
    if len(unknown) > 0:
      print("----------------------------------------", file=dest)
      print("The following utilities have version numbers that could not be ", file=dest)
      print("determined by gkno:", file=dest)
      for dep in unknown:
        print("        ",dep.name, sep="", file=dest)
      print("", file=dest)
      print("This indicates a likely bug or as-yet-unseen oddity.", file=dest)
      print("Please contact the gkno development team to report this issue.  Thanks.", file=dest)
      print("", file=dest)
      print("----------------------------------------", file=dest)
      print("", file=dest)
