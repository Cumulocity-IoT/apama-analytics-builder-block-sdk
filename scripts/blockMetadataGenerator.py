#!/usr/bin/env python

# $Copyright (c) 2019-20 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

import argparse
import logging
import os, glob
import shutil
import sys
import subprocess
import json
import xml.etree.cElementTree as ElementTree
import buildVersions
from subprocess import CalledProcessError
from logging import Formatter
from checkApamaInstallation import confirmFullInstallation

FORMAT = '%(asctime)-15s %(levelname)s : %(message)s'




class Block(object):

	def __init__(self):
		self.data = dict()
		self.data['inputs'] = []
		self.data['outputs'] = []
		self.data['parameters'] = []
		self.idNames = {}

	def setBlockId(self, blockId):
		self.data['id'] = blockId
		return self

	def setBlockName(self, blockName):
		self.data['name'] = blockName
		return self

	def setDescription(self, description):
		if description is not None:
			self.data['description'] = description
		return self

	def setExtendDocs(self, extendedDocumentation):
		if extendedDocumentation is not None:
			self.data['extendedDescription'] = extendedDocumentation
		return self

	def setBlockCategory(self, blockCategory):
		self.data['category'] = blockCategory
		return self

	def setBlockConsumesInput(self):
		self.data['consumesInput'] = True
		return self

	def setBlockProducesOutput(self):
		self.data['producesOutput'] = True
		return self

	def setBlockType(self, blockType):
		if blockType is not None:
			self.data['blockType'] = blockType
		return self

	def setBlockDerivedName(self, derivedName):
		if derivedName is not None:
			self.data['derivedName'] = derivedName
		return self

	def setTitleIsDerived(self, titleIsDerived):
		if titleIsDerived:
			self.data['titleIsDerived'] = True
		return self

	def setBlockReplacementList(self, blockReplace):
		if blockReplace is not None:
			self.data.setdefault('replacesBlocks', []).append(blockReplace)
		return self

	def setInputEventJsonList(self, inputEventList):
		self.data['inputs'].extend(inputEventList)
		return self

	def setOutputEventJsonList(self, outputEventList):
		self.data['outputs'].extend(outputEventList)
		return self

	def setParameterJsonList(self, parameterList):
		self.data['parameters'].extend(parameterList)
		return self

	def getUnderlyingDataMap(self):
		return self.data

	def addId(self, name, type):
		if name in self.idNames: raise NameError('Duplicate name ' + name + ' used as ' + self.idNames[name] + ' and ' + type)
		self.idNames[name] = type


class InputOutputHolder:

	def __init__(self):
		self.data = dict()

	def setInputId(self, eventId):
		self.data['id'] = eventId
		return self

	def setName(self, name):
		self.data['name'] = name
		return self

	def setType(self, type):
		if type=='apama.analyticsbuilder.Value': type = 'any'  # Value is just 'any' with properties, but we only document 'any'.
		self.data['type'] = type
		return self

	def setDescription(self, description):
		if description is not None:
			self.data['description'] = description
		return self

	def setExtendDocumentation(self, extendedDocumentation):
		if extendedDocumentation is not None:
			self.data['extendedDescription'] = extendedDocumentation
		return self

	def getUnderlyingDataMap(self):
		return self.data


class Parameter:

	def __init__(self, ):
		self.data = dict()

	def setParameterId(self, parameterId):
		self.data['id'] = parameterId
		return self

	def setName(self, name):
		self.data['name'] = name
		return self

	def setDescription(self, description):
		if description is not None:
			self.data['description'] = description
		return self

	def setExtendDocumentation(self, extendedDocumentation):
		if extendedDocumentation is not None:
			self.data['extendedDescription'] = extendedDocumentation
		return self

	def setType(self, type):
		self.data['type'] = type
		return self

	def setDefaultValue(self, defaultValue):
		if defaultValue is not None:
			self.data['defaultValue'] = defaultValue
		return self

	def setOptional(self, isOptional):
		if isOptional is not None:
			self.data['optional'] = isOptional
		return self

	def getUnderlyingDataMap(self):
		return self.data

	def setEnumValuesJsonList(self, enumList):
		self.data['enumeratedValues'] = enumList
		return self

	def set(self, name, value):
		if 'Num' in name: value = float(value)
		self.data[name] = value
		return self

	def setHeader(self, name, value):
		hdrs = self.data.get('displayHeaders', dict())
		self.data['displayHeaders'] = hdrs
		hdrs[name] = value
		return self


# If constants <name>_* which start with the same name and are the same type (for string,
# integer, float, boolean) exist for on the parameters,they are enum values.
# Each enumValue has an id (the bit after the underscore), value and name.
class EnumeratedValues:

	def __init__(self):
		self.data = dict()

	def setId(self, enumId):
		self.data['id'] = enumId
		return self

	def setName(self, name):
		self.data['name'] = name
		return self

	def setValue(self, value):
		self.data['value'] = value
		return self

	def setDescription(self, value):
		self.data['description'] = value
		return self

	def getUnderlyingDataMap(self):
		return self.data


class MetaDataHolder:

	def __init__(self):
		self.data = dict()
		self.data['analytics'] = []

	def setVersion(self, version):
		self.data['version'] = version
		return self

	def setBlockList(self, blockDataList):
		self.data['analytics'].extend(blockDataList)
		return self

	def getJson(self):
		return json.dumps(self.data, sort_keys=True, indent=4)

	def writeJsonToFile(self, file):
		json.dump(self.data, file, sort_keys=True, indent=4)


class ValidateBlockDollarFields:

	def __init__(self):
		self.data = dict()
		self.data['$blockCategory'] = False
		self.data['$blockType'] = False
		self.data['$derivedName'] = False
		self.data['$titleIsDerived'] = False
		self.fieldWithMultipleOccurances = ['$replacesBlock', '$consumesInput', '$producesOutput']


packageXPath = "./Package"
blockIdentifierXPath = "./Type[@category='Event']/Member[@name=\"$base\"][@type=\"BlockBase\"][@package='apama.analyticsbuilder']/.."
blockIdentifierXPathAlternate = "./Type[@category='Event']/Member[@name=\"$base\"][@type=\"apama.analyticsbuilder.BlockBase\"]/.."
blockIdentifierCategoryXPath = "./DollarFields/DollarField[@name='$blockCategory']"
blockIdentifierConsumesInputXPath = "./DollarFields/DollarField[@name='$consumesInput']"
blockIdentifierProducesOutputXPath = "./DollarFields/DollarField[@name='$producesOutput']"
blockTypeIdentifierTypeXPath = "./DollarFields/DollarField[@name='$blockType']/Description"
blockTypeIdentifierDerivedNameXPath = "./DollarFields/DollarField[@name='$derivedName']/Description"
blockTypeIdentifierTitleIsDerivedXPath = "./DollarFields/DollarField[@name='$titleIsDerived']/Description"
blockReplacesIdentifierXPath = "./DollarFields/DollarField[@name='$replacesBlock']/Description"
inputIdentifierXPath = "./Action[@name=\"$process\"]/Parameters/Parameter"
inputNameIdentifierXPath = "./Action[@name=\"$process\"]/DollarFields/DollarField[@name=\'$inputName\']/Description"
outputIdentifierXPath = "./Member[@type=\"action\"]"
defaultValueXPath = "./Member[@name=\'{0}\']"
dollarFieldsXPath = "./DollarFields/DollarField"
genericTagXPath = "./DollarFields/DollarField[@name='$%s']/Description"
typeFieldsXPath = "./Package/Type"
vanillaFieldTags = ['semanticType', 'displayType', 'minNumEntries', 'optional']
headerFieldTags = [('displayHeaderName', 'name'), ('displayHeaderValue', 'value')]
validFieldTags = vanillaFieldTags + [x[0] for x in headerFieldTags]


class BlockGenerator:
	## Parse the Description field from XML into name, description and extended documentation
	def _parseDescription(self, descriptionElement, containsName=True):
		descriptionArray = [s.strip('\t" ') for s in descriptionElement.text.splitlines() if s.strip('\t ')]
		name = None
		if containsName and len(descriptionArray) > 0:
			name = descriptionArray[0].strip('.')
			descriptionArray = descriptionArray[1:]
		description = descriptionArray[0] if len(descriptionArray) > 0 else None
		extendDescription = '\n<p></p>\n'.join(descriptionArray[1:]) if len(descriptionArray) > 1 else None
		return name, description, extendDescription

	# Get default value from member type if any
	def _getDefaultValue(self, typeElement, defaultFieldName):
		member = typeElement.find(defaultValueXPath.format(defaultFieldName))
		if member is not None:
			strValue = member.attrib.get('typeValue', '')
			return json.loads(strValue)  # JSON is close enough
		return None

	def _isThisTypeSupported(self, elementType):
		if elementType == 'integer' \
				or elementType == 'float' \
				or elementType == 'string' \
				or elementType == 'any' \
				or elementType == 'boolean':  # sequence <NameValue> is another supported type. see get_member_type()
			return True
		else:
			return False

	# Can be used to create unique hashcode as type and name together can't be duplicated within a particular scope
	def _getTypeUnderscoreName(self, member):
		try:
			parameterType, _, _ = self.get_member_type(member)
			if parameterType is None:  # unlikely to not have a type
				# print('Error getting type or name of the parameter')
				return "" + '_' + member.attrib.get('name').strip('\t ')
			return parameterType + '_' + member.attrib.get('name').strip('\t ')
		except (KeyError, RuntimeError) as err:
			raise Exception('Error getting type or name of the parameter: %s' %err)

	def _getKeyForEnumMapping(self, member):
		# PAM-28925; since enum format is parentParameterName_* , enum values can be matched against these keys.
		return self._getTypeUnderscoreName(member) + '_'

	##  Parse XML Type Element and generate list of Input Objects
	def _createInputElement(self, typeElement, block):
		inputList = []
		# fetch inputName parameters first
		inputNameMap = dict()
		for descriptionElement in typeElement.iterfind(inputNameIdentifierXPath):
			if descriptionElement.text is None or descriptionElement.text.strip() == '':
				continue
			descriptionText = descriptionElement.text.strip()
			seperatorIndex = descriptionText.find(' ')
			if seperatorIndex != -1:
				inputNameMap[descriptionText[:seperatorIndex].strip()] = descriptionText[seperatorIndex:].strip()
			else:
				inputNameMap[descriptionText] = ''

		count = 0
		for parameter in typeElement.iterfind(inputIdentifierXPath):
			if 'name' in parameter.attrib and (len(parameter.attrib['name'].strip()) > 7) and parameter.attrib[
				'name'].startswith('$input_', 0, 7):
				try:
					inputId = parameter.attrib['name'][7:]
					block.addId(inputId, 'input')
					inputPackageName = parameter.get('package', '').strip()

					if inputPackageName != '':
						typePassed = inputPackageName + '.' + parameter.attrib['type']
					else:
						typePassed = parameter.attrib['type']

					defaultValue = self._getDefaultValue(typeElement, '$INPUT_TYPE_' + inputId)
					# Override Type value is a default type is provided
					if defaultValue is not None:
						typePassed = defaultValue
					if typePassed.lower() == 'optional'.lower():  # if input is optional<T> type, then we are interested in only T.
						t = parameter.find('./Parameters/Parameter[@type]')
						if t is not None:
							typePassed = t.attrib['type']
						else:
							self.raiseError("Parameter type for optional type is missing.")


					inputName = inputId
					if inputId in inputNameMap and inputNameMap.get(inputId) != '':
						inputName = inputNameMap.get(inputId)
					inputObject = InputOutputHolder().setInputId(inputId).setType(typePassed).setName(inputName)
					if parameter.find('Description') is not None:
						description = parameter.find('Description')
						(_, descriptionField, extendDocsField) = self._parseDescription(description, containsName=False)
						inputObject.setDescription(descriptionField)
						inputObject.setExtendDocumentation(extendDocsField)

					inputList.append(inputObject.getUnderlyingDataMap())
					count = count + 1
				except (KeyError, RuntimeError) as err:
					print('Error parsing input Elements. Error = %s ' % str(err), file=sys.stderr)
		return inputList

	## Parse XML type element and generate list of Output Objects
	def _createOutputElement(self, typeElement, block):
		outputList = []
		for outputMember in typeElement.iterfind(outputIdentifierXPath):
			if 'name' in outputMember.attrib and (len(outputMember.attrib['name'].strip()) > 11) and \
					outputMember.attrib['name'].startswith('$setOutput_', 0, 11):
				try:
					outputEvent = InputOutputHolder()
					outputId = outputMember.attrib['name'][11:]
					block.addId(outputId, 'output')
					outputEvent.setInputId(outputMember.attrib['name'][11:])

					outputParameterElements = outputMember.findall('./Parameters/Parameter')
					if len(outputParameterElements) != 2:
						print('Incorrect number of arguments found for output type. Argument count %d' % len(outputParameterElements), file=sys.stderr)
						return outputList

					packageName = outputParameterElements[1].get('package', '').strip()
					if packageName != '':
						typePassed = packageName + '.' + outputParameterElements[1].attrib['type']
					else:
						typePassed = outputParameterElements[1].attrib['type']

					defaultValue = self._getDefaultValue(typeElement, '$OUTPUT_TYPE_' + outputId.strip())
					outputEvent.setType(defaultValue if (defaultValue is not None) else typePassed)
					descriptionAll = outputMember.find('Description')
					outputEvent.setName(outputMember.attrib['name'][11:])
					if descriptionAll is not None:
						(nameField, descriptionField, extendDocsField) = self._parseDescription(descriptionAll)
						outputEvent.setDescription(descriptionField)
						outputEvent.setExtendDocumentation(extendDocsField)
						if nameField is not None and nameField != '':
							outputEvent.setName(nameField)
					outputList.append(outputEvent.getUnderlyingDataMap())
				except (KeyError, RuntimeError) as err:
					print('Error parsing output Elements %s ' % str(err), file=sys.stderr)
		return outputList

	# Handles the case the parameter is of type optional/sequence/both.
	def get_member_type(self, member):
		is_optional = False
		member_type = None
		if 'type' not in member.attrib or member.attrib.get('type') is None:
			self.raiseError("Parameter type is missing. ")
		elif member.attrib.get('type').lower() == 'optional'.lower():
			is_optional = True  # optional <T>; note that T may or may not be a sequence.
			t = member.find('./Parameters/Parameter[@type]')
			if t is not None:
				member_type = t.attrib['type']
				if t.attrib.get('type').lower() == 'sequence'.lower():
					seqUnderlyingType = t.find('./Parameters/Parameter[@type]')  # optional <sequence <T> >
					if seqUnderlyingType is not None:
						member_type = seqUnderlyingType.attrib['type']
						return member_type, is_optional, ('NameValue' in member_type or 'LngLat' in member_type)
			else:
				self.raiseError("Parameter type is missing.")
		elif member.attrib.get('type').lower() == 'sequence'.lower():
			t = member.find('./Parameters/Parameter[@type]')
			if t is not None:
				member_type = 'sequence<' + t.attrib['type'] + '>'
				return member_type, is_optional, ('NameValue' in member_type or 'LngLat' in member_type)
			else:
				self.raiseError("Parameter type is missing.")
		else:
			member_type = member.attrib.get('type').strip()
		return member_type, is_optional, (self._isThisTypeSupported(member_type))

	# Create Parameter List
	def _createParameterList(self, typeElement, xmlRootElement, block):
		parameterList = []
		parameterNameSearch = typeElement.attrib.get('name').strip() + '_$Parameters'
		parameterMember = typeElement.find('./Member[@type=\'' + parameterNameSearch + '\']')
		# Fetch the fully qualified name of the parameter from the Block Field Name
		if parameterMember is not None:
			packageName = parameterMember.attrib.get('package', '')
			# Search the XML Tree for any Event of type 'parameterNameSearch' under package 'packageName'
			parameterTypeElement = xmlRootElement.find(
				'./Package[@name=\'' + packageName + '\']/Type[@category=\'Event\'][@name=\'' + parameterNameSearch + '\']')

			if parameterTypeElement is None:
				print('Parameter Element not found in XML. Parameter Type = {0}.{1}'.format(packageName,
				                                                                                        parameterNameSearch), file=sys.stderr)
				return parameterList

			memberToEnumVals = self._createEnumeratedValues(parameterTypeElement)

			for member in parameterTypeElement.iterfind('./Member[@name]'):
				try:
					parameter_type, is_optional_type, is_supported_type = self.get_member_type(member)

					# exclude the constant/non-supported-type parameter
					if 'constant' not in member.attrib \
							and is_supported_type:
						parameterId = member.attrib.get('name').strip('\t ')
						block.addId(parameterId, 'parameter')
						parameterObject = Parameter().setParameterId(parameterId)

						for extraTag in vanillaFieldTags:
							tag = member.find(genericTagXPath % extraTag)
							
							if tag is not None:
								if extraTag == 'optional':
									# If $optional tag is set, make the parameter optional in the UI by
									# setting the optional property to true. Useful for `any` type parameters.
									parameterObject.set(extraTag, True)
								elif tag.text is not None:
									parameterObject.set(extraTag, tag.text.strip())

						for extraTag, name in headerFieldTags:
							tag = member.find(genericTagXPath % extraTag)
							if tag is not None and tag.text is not None:
								parameterObject.setHeader(name, tag.text.strip())

						# check if parameter has default value
						parameterObject.setDefaultValue(
							self._getDefaultValue(parameterTypeElement, '$DEFAULT_' + member.attrib.get('name')))

						if is_optional_type: parameterObject.setOptional(True)
						parameterObject.setType(parameter_type)
						parameterObject.setName(parameterId)

						# get description
						descriptionAll = member.find('Description')
						if descriptionAll is not None:
							(nameField, descriptionField, extendDocsField) = self._parseDescription(descriptionAll)
							parameterObject.setDescription(descriptionField).setExtendDocumentation(extendDocsField)
							# Override Name field with name provided in description
							if nameField is not None and nameField != '':
								parameterObject.setName(nameField)

						# populate the enum list for each applicable member.
						keyForEnumMapping = self._getKeyForEnumMapping(member)
						if keyForEnumMapping in memberToEnumVals and memberToEnumVals[keyForEnumMapping]:
							parameterObject.setEnumValuesJsonList(memberToEnumVals[keyForEnumMapping])

						parameterList.append(parameterObject.getUnderlyingDataMap())
				except (KeyError, RuntimeError) as err:
					print('Error parsing parameter Elements: %s' %err, file=sys.stderr)
		return parameterList

	# Finds and creates enum values, maps them to correct parameter
	def _createEnumeratedValues(self, parameterTypeElement):

		# for string of parent parameter to list of enumValues
		memberToEnumVals = dict()

		# first capture non-constant members into dict as keys.
		for member in parameterTypeElement.iterfind('./Member[@name]'):
			try:
				parameter_type, _, is_supported_type = self.get_member_type(member)
				if 'constant' not in member.attrib \
						and is_supported_type:
					key = self._getKeyForEnumMapping(member)
					memberToEnumVals[key] = []  # populate this list while processing constant members

			except (KeyError, RuntimeError) as err:
				raise Exception('Error parsing parameter Elements: %s' %err)

		keyList = list(memberToEnumVals.keys())
		# Algo in short: Reverse the list to get the longest matching prefix.
		# Let's say, an enum val named 'foobarbar' is up for grabbing, and there exists two
		# parent parameter named 'foo' and 'foobar' of matching type, then in that case
		# the later one i.e. 'foobar' should be the clear winner in grabbing the enum val.
		keyList.sort(reverse=True)

		# now capture matching constant members into dict as corresponding values.
		for member in parameterTypeElement.iterfind('./Member[@name]'):
			try:
				parameter_type, _, is_supported_type = self.get_member_type(member)
				if 'constant' in member.attrib \
						and is_supported_type:

					constVal = self._getTypeUnderscoreName(member)
					for parentMember in keyList:
						if constVal.startswith(parentMember):
							enumId = constVal[
							         len(parentMember):]  # trim out parent-name from the parent-name-prefixed-enums
							enumVal = EnumeratedValues().setId(enumId)  # create the enum value

							descriptionAll = member.find('Description')
							if descriptionAll is not None:
								(nameField, descriptionField, extendDocsField) = self._parseDescription(descriptionAll)
								enumVal.setName(nameField)  # nameField is treated as name in case of enums
								if descriptionField: enumVal.setDescription(descriptionField)  # used for tooltip
							else:
								enumVal.setName(enumId)
								print('No apamadoc found for the name of enum : %s' % member.attrib.get('name').strip('\t '), file=sys.stderr)

							enumVal.setValue(json.loads(member.attrib.get('typeValue')))

							memberToEnumVals[parentMember].append(
								enumVal.getUnderlyingDataMap())  # chain it to corresponding list
							break
			except (KeyError, RuntimeError) as err:
				print('Error parsing parameter Elements: %s' %err, file=sys.stderr)

		return memberToEnumVals

	## create Block object from the xml element passed
	def _createBlock(self, blockId, typeElement, xmlRootElement):

		# set Block Id
		block = Block().setBlockId(blockId)
		# set Block Group
		blockCategory = typeElement.find(blockIdentifierCategoryXPath + '/Description')
		if blockCategory is not None and blockCategory.text is not None:
			block.setBlockCategory(blockCategory.text.strip())

		# check and set consumesInput
		consumesInput = typeElement.find(blockIdentifierConsumesInputXPath)
		if consumesInput is not None:
			block.setBlockConsumesInput()

		# check and set consumesInput
		producesOutput = typeElement.find(blockIdentifierProducesOutputXPath)
		if producesOutput is not None:
			block.setBlockProducesOutput()

		# set Block Type
		blockType = typeElement.find(blockTypeIdentifierTypeXPath)
		if blockType is not None and blockType.text is not None:
			block.setBlockType(blockType.text.strip())
		# set Derived Name for the block
		derivedName = typeElement.find(blockTypeIdentifierDerivedNameXPath)
		if derivedName is not None and derivedName.text is not None:
			block.setBlockDerivedName(derivedName.text.strip())
		# set titleIsDerived Name for the block
		titleIsDerived = typeElement.find(blockTypeIdentifierTitleIsDerivedXPath)
		if titleIsDerived is not None and titleIsDerived.text != 'false':
			block.setTitleIsDerived(titleIsDerived.text.strip())
		# set block to replace.
		replacesBlockList = typeElement.findall(blockReplacesIdentifierXPath)
		for replacesBlock in replacesBlockList:
			if replacesBlock is not None and replacesBlock.text is not None:
				block.setBlockReplacementList(replacesBlock.text.strip())
		# parse description field to blockName, Description and Extended Documentation
		descriptionAll = typeElement.find('Description')
		if descriptionAll is not None and descriptionAll.text is not None:
			(nameField, descriptionField, extendDocsField) = self._parseDescription(descriptionAll)
			block.setBlockName(nameField).setDescription(
				descriptionField if descriptionField is not None else '').setExtendDocs(extendDocsField)
		# set Input Event List
		block.setInputEventJsonList(self._createInputElement(typeElement, block))
		# set Output Events List
		block.setOutputEventJsonList(self._createOutputElement(typeElement, block))
		# set Parameter List
		block.setParameterJsonList(self._createParameterList(typeElement, xmlRootElement, block))

		return block

	## Parse input xmlRootElement and return map of blockId and Block object
	def getAllValidBlockElements(self, xmlRootElement):
		self.validateTags(xmlRootElement)
		blockList = []
		for package in xmlRootElement.findall(packageXPath):
			# search all Events which has 'apama.analytics.BaseBlock $base' member
			eventTypeList = package.findall(blockIdentifierXPath)
			eventTypeList.extend(package.findall(blockIdentifierXPathAlternate))

			for element in eventTypeList:
				# check if Event type contains DollarField blockCategory
				if element.find(blockIdentifierCategoryXPath) is not None:
					if package.attrib['name'].strip() == '':
						raise RuntimeError('Event definition for block should be defined inside a package. Package name is missing for event %s' % element.attrib['name'].strip())
					blockId = package.attrib['name'].strip() + '.' + element.attrib['name'].strip()

					blockObj = self._createBlock(blockId, element, xmlRootElement)
					if blockObj == None:
						print('Error extracting block for event %s' % blockId, file=sys.stderr)
						continue
					blockList.append(blockObj.getUnderlyingDataMap())
				else:
					print('Valid Analytics Builder Block must have $blockCategory tag in apamadocs. Event Name = %s' %
						element.attrib['name'], file=sys.stderr)
		return blockList

	## Parse input XML ElementTree and return the root element
	def getRootElement(self, xmlPath):
		try:
			xmlTree = ElementTree.parse(xmlPath)
			return xmlTree.getroot()
		except:
			raise RuntimeError(sys.exc_info()[1])

	## Validate all the @$tags for their valid names and locations
	def validateTags(self, xmlRootElement):
		parentList = xmlRootElement.findall(typeFieldsXPath)
		for parent in parentList:
			tagsOnEventList = parent.findall(dollarFieldsXPath)
			validator = ValidateBlockDollarFields()
			for dollarTag in tagsOnEventList:
				tagName = dollarTag.attrib['name'].strip()
				if tagName not in validator.fieldWithMultipleOccurances and tagName in validator.data and \
						validator.data[tagName] == True:
					self.raiseError('Multiple tags %s are present in the block' % tagName)
				if tagName in validator.data:
					validator.data[tagName] = True
				description = None
				if dollarTag.find('Description') is not None and dollarTag.find('Description').text is not None:
					description = dollarTag.find('Description').text.strip()

				self.validateTag(parent, None, tagName, description)

			actionTags = parent.findall("./Action")
			for actionTag in actionTags:
				tagsOnActionList = actionTag.findall(dollarFieldsXPath)
				for dollarTag in tagsOnActionList:
					tagName = dollarTag.attrib['name'].strip()
					description = None
					if dollarTag.find('Description') is not None and dollarTag.find('Description').text is not None:
						description = dollarTag.find('Description').text.strip()

					self.validateTag(actionTag, parent, tagName, description)

			memberTags = parent.findall("./Member")
			for memberTag in memberTags:
				tagsOnMemberList = memberTag.findall(dollarFieldsXPath)
				for dollarTag in tagsOnMemberList:
					tagName = dollarTag.attrib['name'].strip()
					description = None
					if dollarTag.find('Description') is not None and dollarTag.find('Description').text is not None:
						description = dollarTag.find('Description').text.strip()

					self.validateTag(memberTag, parent, tagName, description)

	def validateCategoryOrTypeName(self, parentElement, grandParentElement, tagName, description):
		if 'category' not in parentElement.attrib or not parentElement.attrib[
			                                                 'category'] == 'Event' or parentElement.find(
			'./Member[@name=\"$base\"]') is None:
			parentName = self.getElementName(parentElement)
			grandParentName = self.getElementName(grandParentElement)
			errorMessage = self.createErrorMessage(parentName, grandParentName, tagName,
			                                       description) + ' This is only valid on a block event which has a member \'$base\'.'
			self.raiseError(errorMessage)

	def validateActionName(self, actionElement, eventElement, tagName, description):
		if 'name' not in actionElement.attrib or not actionElement.attrib['name'] == '$process':
			parentName = self.getElementName(actionElement)
			grandParentName = self.getElementName(eventElement)
			errorMessage = self.createErrorMessage(parentName, grandParentName, tagName,
			                                       description) + ' This is only valid on a $process action.'
			self.raiseError(errorMessage)

	def validateMemberTagName(self, memberElement, eventElement, tagName, description):
		if not memberElement.tag == 'Member':
			parentName = self.getElementName(memberElement)
			grandParentName = self.getElementName(eventElement)
			errorMessage = self.createErrorMessage(parentName, grandParentName, tagName,
			                                       description) + ' This is only valid on an event field.'
			self.raiseError(errorMessage)

	def raiseError(self, errorMessage):
		raise RuntimeError('Invalid tag present in the monitor file. Error = %s' % errorMessage)

	def getElementName(self, element):
		if element is not None and 'name' in element.attrib:
			return element.attrib['name']
		else:
			return None

	def createErrorMessage(self, parentName, grandParentName, tagName, description):
		if description is not None and grandParentName is not None:
			errorMessage = '\'%s\' tag with description \'%s\' present on \'%s\' inside the event \'%s\' is not valid.' % (
				tagName, description, parentName, grandParentName)
		elif description is not None:
			errorMessage = '\'%s\' tag with description \'%s\' present on \'%s\' is not valid.' % (
				tagName, description, parentName)
		elif grandParentName is not None:
			errorMessage = '\'%s\' tag present on \'%s\' inside the event \'%s\' is not valid.' % (
				tagName, parentName, grandParentName)
		else:
			errorMessage = '\'%s\' tag present on \'%s\' is not valid.' % (tagName, parentName)

		return errorMessage

	def validateTag(self, tagParent, tagGrandParent, tagName, tagDescription):
		validator = ValidateBlockDollarFields()
		if tagName in list(validator.data.keys()) or tagName in validator.fieldWithMultipleOccurances:
			self.validateCategoryOrTypeName(tagParent, tagGrandParent, tagName, tagDescription)
		elif tagName == '$inputName':
			self.validateActionName(tagParent, tagGrandParent, tagName, tagDescription)
		elif tagName in ['$' + x for x in validFieldTags]:
			self.validateMemberTagName(tagParent, tagGrandParent, tagName, tagDescription)
		else:
			parentName = self.getElementName(tagParent)
			grandParentName = self.getElementName(tagGrandParent)
			errorMessage = self.createErrorMessage(parentName, grandParentName, tagName, tagDescription)
			self.raiseError(errorMessage)






class ScriptRunner:
	def __init__(self, apama_home, java_home, outputFile, inputDir, tmpDir, version):
		self.apamaHome = apama_home
		self.javaHome = java_home
		self.outputFile = os.path.abspath(outputFile)
		self.inputDir = os.path.abspath(inputDir)
		self.tmpDir = os.path.abspath(tmpDir)
		self.scriptVersion = version


	nestedProperties = ['inputs', 'outputs', 'parameters']
	simpleProperties = ['name', 'description', 'extendedDescription', 'displayType', 'derivedName']
	uniqueIdentifiers = ['blockType', 'id']
	DISPLAY_HEADER = 'displayHeaders'
	DISPLAY_HEADER_KEYS = ['name', 'value']
	BLOCK_PREFIX = 'block'
	SEP_UNDERSCORE = '_'
	ENCODING = 'utf8'
	ENUM_VAL='enumeratedValues'
	ENUM = 'enums'

	def _mangleBraces(self, str):
		ret=''
		for c in str:
			if c=='{' or c=='}':
				ret=ret+'{{'+c+'}}'
			else:
				ret=ret+c
		return ret

	def _extractProperty(self, object, message_id, uniqueIdentifier, simpleProperties):

		"""Extracts the simple properties from the object."""
		results={}
		for obj in object:
			if uniqueIdentifier not in obj:
				continue
			obj_id = message_id + self.SEP_UNDERSCORE + obj[uniqueIdentifier]
			for property in simpleProperties:
				if property in obj:
					prop_val = obj[property]				
					results.update({obj_id + self.SEP_UNDERSCORE + property:self._mangleBraces(prop_val)})
			if self.ENUM_VAL in obj:
				res=self._extractProperty(obj[self.ENUM_VAL], message_id+ self.SEP_UNDERSCORE+ obj[uniqueIdentifier]+ self.SEP_UNDERSCORE + self.ENUM, uniqueIdentifier, simpleProperties )
				results.update(res)
			if self.DISPLAY_HEADER in obj:
				dispobj = obj[self.DISPLAY_HEADER]
				for p in self.DISPLAY_HEADER_KEYS:
					if p in dispobj:
						results.update({obj_id + self.SEP_UNDERSCORE + self.DISPLAY_HEADER + self.SEP_UNDERSCORE + p: self._mangleBraces(dispobj[p])})
		return results

	def _generateJSONoutput(self, structureXMLPath):
		blockGeneratorLogic = BlockGenerator()
		metaDataHolder = MetaDataHolder()
		metaDataHolder.setVersion(self.scriptVersion)
		root = blockGeneratorLogic.getRootElement(structureXMLPath)
		if root is None:
			raise Exception('Cannot generate block metadata because of empty structure.xml file: %s', structureXMLPath)
		blockList = blockGeneratorLogic.getAllValidBlockElements(root)
		metaDataHolder.setBlockList(blockList)

		with open(self.outputFile, 'w') as file:
			metaDataHolder.writeJsonToFile(file)
		messages={}
		for block in blockList:
			block_id =  self.BLOCK_PREFIX + self.SEP_UNDERSCORE + block[self.uniqueIdentifiers[1]]
			for property in self.simpleProperties:
				if property in block:
					prop_val = block[property]
					messages.update({block_id + self.SEP_UNDERSCORE + property : self._mangleBraces(prop_val)})
			
			for property in self.nestedProperties:
				r = self._extractProperty(block[property], block_id + self.SEP_UNDERSCORE + property, self.uniqueIdentifiers[1], self.simpleProperties)
				messages.update(r)

		return (messages, blockList)

	#Generate Apama Docs for each Catalog list and parse the structure.xml to create Block JSON file
	def _generateApamaDocs(self):
		"""
		Generate Apama Doc for all the monitors in the specified directory.
		:return: Path to the generated structure.xml
		"""
		confirmFullInstallation()
		apamaDocErrLog = os.path.join(self.tmpDir, 'apamadoc_err.log')
		apamaDocOutLog = os.path.join(self.tmpDir, 'apamadoc_out.log')
		
		apamaDocOutput = os.path.join(self.tmpDir, 'apamadoc')
		if not os.path.exists(apamaDocOutput):
			os.makedirs(apamaDocOutput)
		cmd = [
			os.path.join(self.javaHome, 'bin', 'java'),
			'-DAPAMA_HOME=' + self.apamaHome,
			'-Djava.awt.headless=true',
			'-jar',
			os.path.join(self.apamaHome, 'lib', 'ap-generate-apamadoc.jar'),
			apamaDocOutput,
			self.inputDir,
		]

		with open(apamaDocErrLog, 'w+') as errFile:
			with open(apamaDocOutLog, 'w+') as outFile:
				try:
					subprocess.check_call(cmd, stderr=errFile, stdout=outFile)
				except CalledProcessError as err:
					print('Error while generating Apama Doc from %s. Please check %s file for more details' %
						(self.inputDir, os.path.abspath(apamaDocErrLog)), file=sys.stderr)
					raise err
		return os.path.join(apamaDocOutput, 'structure.xml')

	
	#validate Catalog path and calls _generateApamaDocs to generate Apamadocs and then Metadata json
	def generateBlockMetaData(self):
		if not list(glob.glob(self.inputDir + '/**/*.mon', recursive=True)): 
			print("No input files found", file=sys.stderr)
			return (None, {})
		structureXml = self._generateApamaDocs()
		if os.path.isfile(structureXml):
			(msgs, blocks)=self._generateJSONoutput(structureXml)
		else:
			raise Exception('Cannot generate block metadata because %s file was not generated', structureXml)
		return (self.outputFile, msgs)

class STDOUTFilter(logging.Filter):
	def filter(self, record):
		return record.levelno == logging.INFO

def add_arguments(parser):
	parser.add_argument('--input', metavar='DIR', type=str, required=True, help='the input directory containing blocks')
	parser.add_argument('--output', metavar='JSON_FILE', type=str, required=True, help='the output JSON file containing the metadata for blocks')

def run_metadata_generator(input, output, tmpDir, printMsg=False):
	confirmFullInstallation()
	apama_home = os.getenv('APAMA_HOME', None)
	# assumes we're running with apama_env sourced
	if 'APAMA_JRE' in os.environ:
		java_home = os.environ['APAMA_JRE']
	else:
		# else in the docker image
		java_home = os.path.join(apama_home,'..', 'jvm', 'jvm')


	inputDir = os.path.abspath(os.path.normpath(input))
	if not os.path.isdir(inputDir): raise Exception('The input directory does not exist: %s' % inputDir)

	output = os.path.normpath(output)
	if not output.endswith('.json'):
		output += '.json'

	scriptRunner = ScriptRunner(apama_home, java_home, output,
	                            inputDir, tmpDir, buildVersions.FULL_VERSION)
	f = scriptRunner.generateBlockMetaData()
	if printMsg:
		if f[0]:
			print(f'Created {f[0]}')
		else:
			print('No blocks found')
	return f


def run(args):
	return run_metadata_generator(args.input, args.output, args.tmpDir, printMsg=True)

## Main method
if __name__ == '__main__':
	assert 'APAMA_JRE' in os.environ, 'APAMA_JRE variable is not set.'
	
	## Parse Command line arguments
	parser = argparse.ArgumentParser(description='Analytics Builder Block Metadata Generator')
	add_arguments(parser)
	run(parser.parse_args())

	
