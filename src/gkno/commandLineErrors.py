#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class commandLineErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '3'

  # If a tool is added, but the tool is already available.
  def invalidCommandLine(self):
    self.text.append('Invalid command line.')
    self.text.append('The supplied command line is invalid. Please check the syntax and correct any errors. For additional help, see the ' + \
    'documentation, or type gkno --help.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a command line argument is invalid.
  def invalidArgument(self, argument):
    self.text.append('Invalid argument on the command line.')
    self.text.append('The supplied command line contains the argument \'' + argument + '\', but this is not a valid argument. Please use ' + \
    '\'--help\' on the command line to see all of the available arguments and correct the command line.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a value provided on the command line is of the wrong type.
  def invalidValue(self, longFormArgument, shortFormArgument, value, dataType, isGkno):

    # Add an additional piece of text to distinguish gkno specific arguments.
    text = 'gkno specific ' if isGkno else ''
    self.text.append('Invalid value on the command line.')

    # Give an error if no value was provided, where one is necessary.
    if not value:
      self.text.append('The ' + text + 'argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' was not given a value. This argument ' + \
      'expects values with the type \'' + dataType + '\'. Please check the command line and ensure that all arguments are given appropriate values.')

    # If the provided value is of the wrong type.
    else:
      self.text.append('The ' + text + 'argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' was given the value \'' + value + \
      '\', which has the wrong data type. This argument expects values with the type \'' + dataType + '\'. Please check the arguments given on ' + \
      'command line.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # Multiple parameter sets are defined.
  def multipleParameterSets(self):
    self.text.append('Multiple parameter set defined')
    self.text.append('The command line argument \'--parameter-set (-ps)\' can be used to define a predefined set of parameters to use. ' + \
    'Multiple parameter sets have been defined on the command line, but it is only permissable to define a single set. Please ensure that only ' + \
    'one parameter set is defined on the command line. If no parameter set exists containing all of the desired parameters, it is possible to ' + \
    'generate a new parameter set by defining all the required parameters on the command line and then using the \'--export-parameter-set (-ep)\' ' + \
    'argument to define a name for the new parmater set.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # Multiple arguments have been given multiple values and this cannot be processed.
  def multipleArgumentsWithMultipleValues(self, task, arguments):
    self.text.append('Multiple arguments given multiple values.')
    self.text.append('As part of the pipeline, the task \'' + task + '\' has multiple arguments with multiple specified values. The arguments in ' + \
    'question are:')
    self.text.append('\t')
    for argument in arguments: self.text.append('\t' + argument)
    self.text.append('\t')
    self.text.append('There are cases where it is permitted for multiple arguments to have multiple values, but these conditions are not ' + \
    'satisfied in this case. Please check the command line for errors, and check the documentation to determine the cases in which supplying ' + \
    'multiple value is permitted.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a pipeline is rerun, but there are no (or multiple) makefiles already available for the pipeline.
  def cannotRerunPipeline(self, pipeline):
    self.text.append('Unable to rerun pipeline.')
    self.text.append('When rerunning a pipeline, gkno searches for a file of the form <pipeline>.<random string>.make. If found, gkno will extract the ' + \
    'random string and use it again to rerun the pipeline. This ensures that the makefile itself is replaced, rather than a new one being generated, ' + \
    'and that any temporary files generated by the pipeline will include this string. If this does not occur, any files created by the previous pipeline ' + \
    'execution, will not be identified and so they will also be regenerated, wasting time and resources.')
    self.text.append('\t')
    self.text.append('The current directory contains either no, or multiple files of the required form, and so the pipeline cannot be rerun. If the pipeline ' + \
    'needs to be rerun, please remove files from the current directory to ensure that the correct pipeline is rerun.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)
