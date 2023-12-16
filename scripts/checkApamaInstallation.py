#!/usr/bin/env python3

# $Copyright (c) 2023 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

import os

def confirmFullInstallation():
	apama_home = os.getenv('APAMA_HOME', None)
	if not apama_home: raise Exception('Run this script from an apama_env shell or from the Apama Command Prompt of a full Apama installation.')
	if not os.path.exists(apama_home): raise Exception('APAMA_HOME path does not exist: %s' % apama_home)
	# Now check that the installation is full Apama installation.
	# To check for full Apama installation, check for existence of a file which is present
	# only in the full installation.
	fileToCheck = 'lib/ap-generate-apamadoc.jar'
	if not os.path.exists(os.path.join(apama_home, fileToCheck)):
		raise Exception("Full Apama installation is required to run this command.")
