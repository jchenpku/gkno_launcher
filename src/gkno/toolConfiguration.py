#!/bin/bash/python

from __future__ import print_function

import fileHandling
import generalConfigurationFileMethods as methods
import parameterSets
import toolConfigurationErrors as errors

import json
import os
import sys

# Define a class to hold information on the arguments.
class argumentAttributes:
  def __init__(self):
    
    # If an argument is allowed to be set multiple times.
    self.allowMultipleValues = False

    # Store the defined long and short form of the argument recognised as well
    # as the argument expected by the tool.
    self.commandLineArgument = None
    self.longFormArgument    = None
    self.shortFormArgument   = None

    # Instructions on how to modify the argument and the value to be used on
    # the command line in the makefile.
    self.modifyArgument = None
    self.modifyValue    = None

    # Some tools output files to stdout. If this is the case, record that fact so that
    # the command line can be built accordingly.
    self.isStdout = False

    # Mark the edge as a stream if necessary.
    self.isStream = False

    # Store instructions on how to modify the argument and the value if the tool is
    # accepting a stream as input or is outputting to a stream.
    self.inputStreamInstructions  = {}
    self.outputStreamInstructions = {}

    # Define the extensions allowed for the argument.
    self.extensions = []

    # Store instructions on how to construct the filename.
    self.constructionInstructions = None

    # Record the argument description.
    self.description = None

    # Store the data type of the value supplied with this argument.
    self.dataType = None

    # Keep track of required arguments.
    self.isRequired = False

    # Record id the argument points to a filename stub and store the 
    # associated extensions. Also, store the extension for this specific node.
    self.isStub          = False
    self.primaryStubNode = False
    self.stubExtension   = None
    self.stubExtensions  = []
    self.includeStubDot  = True

    # Record the category to which the argument belongs.
    self.category = None

    # Record if the argument is for an input or output file.
    self.isInput  = False
    self.isOutput = False

    # Store if the argument is greedy (e.g. uses all values associated with the node).
    self.isGreedy = False

    # Store whether the argument can be suggested as a possible tool to use in a
    # pipeline builder.
    self.isSuggestible = False

    # Record if the value supplied on the command line should be included in quotations when included
    # in the command line in the makefile.
    self.includeInQuotations = False

    # Record whether the node associated with this argument should be included in a reduced plot.
    self.includeInReducedPlot = True

# Define a class to hold information about the tool.
class toolAttributes:
  def __init_(self):
    pass

# Define a class to store general pipeline attributes,
class toolConfiguration:
  def __init__(self):

    # Define error handling.
    self.errors = errors.toolErrors()

    # Record the name of the tool.
    self.name = None

    # Record the tool ID.
    self.id = None

    # Define the arguments associated with the tool.
    self.arguments = {}

    # Define the order in which the argument should be written.
    self.argumentOrder = []

    # Define the delimiter between the argument and the value on the
    # tool commmand line. This is usually a space.
    self.delimiter = ' '

    # A description of the tool.
    self.description = None

    # The categories to which the tool belongs.
    self.categories = ['General']

    # The tool executable, its path and any modifiers.
    self.executable = None
    self.modifier   = None
    self.path       = None
    self.precommand = None

    # Record if this tool is hidden in the help.
    self.isHidden = False

    # Some tools do not produce any outputs. If this is the case, the tool has to
    # be marked.
    self.noOutput = False

    # Store the tools that need to be compiled for this tool to be available.
    self.requiredCompiledTools = []

    # Store the URL for the tool.
    self.url = None

    # If the tool is untested, but available, the isExperimental flag can be set. This
    # will ensure that the tool is listed as experimental and urge caution in its use.
    self.isDevelopmental = False

    # The parameter set information for this pipeline.
    self.parameterSets = parameterSets.parameterSets()

    # It is sometimes desirable to allow all steps to be processed without termination. Other
    # times, if a problem is encountered, execution should terminate. Keep track of this.
    self.allowTermination = True

    # As pipeline configuration files are processed, success will identify whether a problem was
    # encountered.
    self.success = True

  # Check that a supplied configuration file is a tool configuration file.
  def checkConfigurationFile(self, filename):

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, True)

    # Check that the configuration file is for a pipeline.
    try: configurationType = data['configuration type']
    except: return False
    if configurationType != 'tool': return False
    return True

  # Open a configuration file, process the data and return.
  def getConfigurationData(self, tool, filename):

    # Store the name of the tool.
    self.name = tool

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, True)

    # Process the configuration file data.
    success = self.processConfigurationFile(data)

  # Process the configuration file.
  def processConfigurationFile(self, data):

    # Check that the configuration file is a pipeline configuration file.
    self.checkIsTool(data)

    # Check the top level information, e.g. pipeline description.
    self.checkTopLevelInformation(data)

    # Validate input arguments.
    if self.success: self.checkInputArguments(data['arguments'])

    # Validate output arguments.
    if self.success: self.checkOutputArguments(data['arguments'])

    # Validate all other arguments.
    if self.success: self.checkRemainingArguments(data['arguments'])

    # Check that certain required combinations of attributes are adhered to.
    if self.success: self.checkAttributeCombinations()

    # There are occasions where a particular attribute value can force the value of
    # another. Check for these cases and force the values as required. As an example,
    # if the 'command line argument' attribute is set to 'none', then the argument
    # will not be written to the command line. If the 'modify argument' attribute is
    # unset, it can be set to 'omit' in this instance
    if self.success: self.forceAttributes()

    # Check the values supplied to attributes.
    if self.success: self.checkAttributeValues()

    # Check the parameter set information and store.
    if self.success: self.success = self.parameterSets.checkParameterSets(data['parameter sets'], self.allowTermination, self.name, isTool = True)

  # Check that the configuration file is for a tool.
  def checkIsTool(self, data):

    # Get the configuration type field. If this is not present, terminate, since this is the field that
    # defines if the configuration file is for a tool or for a pipeline.
    try: configurationType = data['configuration type']
    except: self.errors.noConfigurationType(self.name)

    if configurationType != 'tool': self.errors.invalidConfigurationType(self.name, configurationType)

  # Process the top level pipeline configuration information.
  def checkTopLevelInformation(self, data):

    # Define the allowed general attributes.
    allowedAttributes                       = {}
    allowedAttributes['arguments']          = (dict, True, False, None)
    allowedAttributes['argument delimiter'] = (str, False, True, 'delimiter')
    allowedAttributes['argument order']     = (list, False, True, 'argumentOrder')
    allowedAttributes['categories']         = (list, True, True, 'categories')
    allowedAttributes['configuration type'] = (str, True, False, None)
    allowedAttributes['description']        = (str, True, True, 'description')
    allowedAttributes['developmental']      = (bool, False, True, 'isDevelopmental')
    allowedAttributes['executable']         = (str, True, True, 'executable')
    allowedAttributes['hide tool']          = (bool, False, True, 'isHidden')
    allowedAttributes['id']                 = (str, True, True, 'id')
    allowedAttributes['parameter sets']     = (list, True, False, None)
    allowedAttributes['modifier']           = (str, False, True, 'modifier')
    allowedAttributes['path']               = (str, True, True, 'path')
    allowedAttributes['precommand']         = (str, False, True, 'precommand')
    allowedAttributes['tools']              = (list, True, True, 'requiredCompiledTools')
    allowedAttributes['url']                = (str, False, True, 'url')

    # Define a set of information to be used in help messages.
    helpInfo = (self.name, None, None)

    # Check the attributes against the allowed attributes and make sure everything is ok.
    self = methods.checkAttributes(data, allowedAttributes, self, self.allowTermination, helpInfo)

  # Validate the contents of all input arguments.
  def checkInputArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values']         = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument']         = (str, True, True, 'commandLineArgument')
    allowedAttributes['construct filename']            = (dict, False, True, 'constructionInstructions')
    allowedAttributes['data type']                     = (str, True, True, 'dataType')
    allowedAttributes['description']                   = (str, True, True, 'description')
    allowedAttributes['extensions']                    = (list, False, True, 'extensions')
    allowedAttributes['if input is stream']            = (dict, False, True, 'inputStreamInstructions')
    allowedAttributes['include dot in stub extension'] = (bool, False, True, 'includeStubDot')
    allowedAttributes['include in reduced plot']       = (bool, False, True, 'includeInReducedPlot')
    allowedAttributes['include value in quotations']   = (bool, False, True, 'includeInQuotations')
    allowedAttributes['is filename stub']              = (bool, False, True, 'isStub')
    allowedAttributes['long form argument']            = (str, True, True, 'longFormArgument')
    allowedAttributes['modify argument']               = (str, False, True, 'modifyArgument')
    allowedAttributes['modify value']                  = (str, False, True, 'modifyValue')
    allowedAttributes['required']                      = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']           = (str, False, True, 'shortFormArgument')
    allowedAttributes['stub extensions']               = (list, False, True, 'stubExtensions')
    allowedAttributes['suggestible']                   = (bool, False, True, 'isSuggestible')

    # Fail if there is no input arguments section. This is included since all input arguments
    # are included in the 'Inputs' section and, if by mistake, the section is named 'inputs' (no
    # capitalisation), input arguments will be miscategorised.
    if 'Inputs' not in arguments: self.errors.missingArgumentSection(self.name, 'Inputs')

    # Check the arguments.
    self.checkArguments('Inputs', arguments['Inputs'], allowedAttributes, isInput = True, isOutput = False)

  # Validate the contents of all input arguments.
  def checkOutputArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values']         = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument']         = (str, True, True, 'commandLineArgument')
    allowedAttributes['construct filename']            = (dict, False, True, 'constructionInstructions')
    allowedAttributes['data type']                     = (str, True, True, 'dataType')
    allowedAttributes['description']                   = (str, True, True, 'description')
    allowedAttributes['extensions']                    = (list, False, True, 'extensions')
    allowedAttributes['include dot in stub extension'] = (bool, False, True, 'includeStubDot')
    allowedAttributes['include in reduced plot']       = (bool, False, True, 'includeInReducedPlot')
    allowedAttributes['include value in quotations']   = (bool, False, True, 'includeInQuotations')
    allowedAttributes['is filename stub']              = (bool, False, True, 'isStub')
    allowedAttributes['if output to stream']           = (dict, False, True, 'outputStreamInstructions')
    allowedAttributes['long form argument']            = (str, True, True, 'longFormArgument')
    allowedAttributes['modify argument']               = (str, False, True, 'modifyArgument')
    allowedAttributes['modify value']                  = (str, False, True, 'modifyValue')
    allowedAttributes['output to stdout']              = (bool, False, True, 'isStdout')
    allowedAttributes['required']                      = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']           = (str, False, True, 'shortFormArgument')
    allowedAttributes['stub extensions']               = (list, False, True, 'stubExtensions')

    # Fail if there is no output arguments section. This is included since all output arguments
    # are included in the 'Outputs' section and, if by mistake, the section is named 'outputs' (no
    # capitalisation), output arguments will be miscategorised.
    if 'Outputs' not in arguments: self.errors.missingArgumentSection(self.name, 'Outputs')

    # Check the arguments.
    self.checkArguments('Outputs', arguments['Outputs'], allowedAttributes, isInput = False, isOutput = True)

  # Validate the contents of all input arguments.
  def checkRemainingArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values']       = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument']       = (str, True, True, 'commandLineArgument')
    allowedAttributes['data type']                   = (str, True, True, 'dataType')
    allowedAttributes['description']                 = (str, True, True, 'description')
    allowedAttributes['extensions']                  = (list, False, True, 'extensions')
    allowedAttributes['include in reduced plot']     = (bool, False, True, 'includeInReducedPlot')
    allowedAttributes['include value in quotations'] = (bool, False, True, 'includeInQuotations')
    allowedAttributes['long form argument']          = (str, True, True, 'longFormArgument')
    allowedAttributes['modify argument']             = (str, False, True, 'modifyArgument')
    allowedAttributes['modify value']                = (str, False, True, 'modifyValue')
    allowedAttributes['required']                    = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']         = (str, False, True, 'shortFormArgument')

    # Loop over all the other categories of arguments.
    for category in arguments:
      if category != 'Inputs' and category != 'Outputs':

        # Check the arguments.
        self.checkArguments(category, arguments[category], allowedAttributes, isInput = False, isOutput = False)

  # Check the contents of the arguments.
  def checkArguments(self, category, arguments, allowedAttributes, isInput, isOutput):

    # Loop over all of the input arguments and check their validity.
    for argumentInformation in arguments:

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'arguments', None)

      # Define a class to store task attribtues.
      attributes = argumentAttributes()

      # Check all the supplied attributes.
      self.success, attributes = methods.checkAttributes(argumentInformation, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # Check that the argument name is unique.
      if attributes.longFormArgument in self.arguments:
        #TODO ERROR
        if self.allowTermination: print('tools.checkArguments - 1', attributes.longFormArgument); exit(0)
        else:
          self.success = False
          return

      # Define the argument category.
      attributes.category = category

      # Store the attributes for the argument.
      if isInput: attributes.isInput = True
      elif isOutput: attributes.isOutput = True
      self.arguments[attributes.longFormArgument] = attributes

  # Check that required attributes combinations are available. For example, if the 'is filename stub'
  # attribute is set, the stub extensions field must also be present.
  def checkAttributeCombinations(self):

    # Loop over all the arguments.
    for argument in self.arguments:

      # If isStub is set, 
      if self.getArgumentAttribute(argument, 'isStub') and not self.getArgumentAttribute(argument, 'stubExtensions'):
        if self.allowTermination: self.errors.noExtensionsForStub(self.name, argument)
        else:
          self.success = False
          return

  # Force attribute values based on set values.
  def forceAttributes(self):
    for argument in self.arguments:

      # If the 'command line argument' is set to none and 'modify argument' is unset, force 'modify
      # argument' to be set to 'omit'.
      if self.getArgumentAttribute(argument, 'commandLineArgument') == 'none' and not self.getArgumentAttribute(argument, 'modifyArgument'):
        self.setArgumentAttribute(argument, 'modifyArgument', 'omit')

  # Check that the values given to certain attributes are valid.
  def checkAttributeValues(self):

    # Loop over all the arguments.
    for argument in self.arguments:

      # If modify argument is populated, check that the supplied value is valid.
      value = self.getArgumentAttribute(argument, 'modifyArgument')
      if value:
  
        # Define the valid values.
        validValues = [
                        'omit'
                      ]
  
        # Check that the supplied value is valid.
        #TODO ERROR
        if value not in validValues:
          if self.allowTermination: self.errors.invalidValues(self.name, argument, 'modifyArgument', value, validValues)
          else:
            self.success = False
            return False

  ##############################
  ### Get and set attributes ###
  ##############################

  # Get an argument attribute.
  def getArgumentAttribute(self, argument, attribute):
    try: return getattr(self.arguments[argument], attribute)
    except: return None

  # Set an argument attribute.
  def setArgumentAttribute(self, argument, attribute, value):
    setattr(self.arguments[argument], attribute, value)

  # Return the long form version of an argument.
  def getLongFormArgument(self, argument):

    # Loop over all the arguments and see if the argument corresponds to a long
    # or short form version.
    for longFormArgument in self.arguments.keys():
      if argument == longFormArgument: return longFormArgument

      # Get the short form version of the argument and check if the argument matches this.
      shortFormArgument = self.getArgumentAttribute(longFormArgument, 'shortFormArgument')
      if argument == shortFormArgument: return longFormArgument

    # If no match was found, return None.
    return None

  # Return the data structure containing all the information on the requested argument.
  def getArgumentData(self, argument):
    try: return self.arguments[argument]
    except: return None

  ######################
  ### Static methods ###
  ######################

  # Get an argument attribute from supplied attributes
  def getArgumentAttributeFromSupplied(attributes, attribute):
    try: return getattr(attributes.arguments[argument], attribute)
    except: return False
