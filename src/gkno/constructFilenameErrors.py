#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class constructFilenameErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '15'

  ##################################
  ## Errors with top level fields ##
  ##################################

  # If the extension could not be identified.
  def unableToRetrieveExtension(self, task, argument, filename, extensions):
    self.text.append('Unable to identify filename extension when constructing filename.')
    self.text.append('The file associated with the pipeline task \'' + task + '\', argument \'' + argument + \
    '\' is constructed using the name of a file already used in the pipeline. The file used as a template ' + \
    'for the construction has the name \'' + filename + '\'.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If values from a different argument are being added to the filename, but the argument is invalid.
  def invalidArgument(self, task, tool, argument, useArgument):
    self.text.append('Invalid argument in construction instructions')
    self.text.append('As part of the pipeline, the task \'' + task + '\' uses the tool \'' + tool + '\'. The ' + \
    'argument \'' + argument + '\' has its values constructed using instructions contained in the tool configuration ' + \
    'file. As part of the construction, values from other tool arguments are used. In particular, the argument \'' + \
    useArgument + '\' is specified, but this is not a valid argument for the tool. Please ensure that all construction ' + \
    'instructions in the configuration file contain valid information.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # Values from another argument are to be built into the filename, but the argument whose values are to be used
  # has not been set.
  def noArgumentValuesToBuild(self, task, argument, constructionArgument):
    self.text.append('Error constructing values for argument.')
    self.text.append('No values for the argument \'' + argument + '\' used by the task \'' + task + '\' were set on the ' + \
    'command line and so values are constructed using instructions from the configuration file. The instructions use ' + \
    'the values given to another argument \'' + constructionArgument + '\' (note that this is the argument defined for the ' + \
    'and may be different, or even not present, at the pipeline level), but no values were specified for this argument.')
    self.text.append('\tIt is preferable to ensure that this error cannot occur, so ensure that the value required to ' + \
    'construct the filename is listed as required in either the tool or the pipeline configuration file, or that a default' + \
    'value is provided in the parameter sets.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)
