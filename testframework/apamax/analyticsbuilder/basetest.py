#!/usr/bin/env python
## License
# Copyright (c) 2017-2022 Software AG, Darmstadt, Germany and/or its licensors

# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
# https://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


from pysys.constants import *
from pysys.basetest import BaseTest
from apama.correlator import CorrelatorHelper
from apama.basetest import ApamaBaseTest
import os, zipfile, json
from pathlib import Path
import math

class Waiter:
	def __init__(self, parent, corr, channels=[]):
		self.parent = parent
		self.corr = corr
		self.stdouterr = self.parent.allocateUniqueStdOutErr('waiter')

		corr.receive(self.stdouterr[0], channels=channels, utf8=True)
	def waitFor(self, expr, count=5, errorExpr=None):
		self.corr.flush(count=count)
		if errorExpr==None:
			self.parent.waitForSignal(self.stdouterr[0], expr=expr)
		else:
			self.parent.waitForSignal(self.stdouterr[0], expr=f'({expr})|({errorExpr})')
			self.parent.assertGrep(self.stdouterr[0], expr=errorExpr, contains=False)

class AnalyticsBuilderBaseTest(ApamaBaseTest):
	"""
	Base test for Analytics Builder tests.

	Requires the following to be set on the project in pysysproject.xml file (typically from the environment):
	ANALYTICS_BUILDER_SDK
	APAMA_HOME
	"""

	def __init__(self, descriptor, outsubdir, runner, **kwargs):
		super(AnalyticsBuilderBaseTest, self).__init__(descriptor, outsubdir, runner, **kwargs)
		self.modelId=0
		self.IS_WINDOWS = OSFAMILY=='windows'

	def runAnalyticsBuilderScript(self, args=[], environs={}, **kwargs):
		"""
		Run the analytics_builder script.
		:param args: The arguments to pass to the script.
		:param environs: Any environment overrides.
		:param kwargs: Any arguments to pass through to startProcess.
		:return: The process handle of the process (L{ProcessWrapper}).
		"""
		env = dict(os.environ)
		env['PYTHONDONTWRITEBYTECODE'] = 'true'  # .pyc optimizations not needed and make it harder to delete things later
		if environs: env.update(environs)
		script = 'analytics_builder'
		stdouterr = self.allocateUniqueStdOutErr(script)

		try:
			result=self.startProcess(f'{self.project.ANALYTICS_BUILDER_SDK}/{script}'+('.cmd' if self.IS_WINDOWS else ''), args,
				stdout=stdouterr[0], stderr=stdouterr[1],
				displayName=script, environs=env, **kwargs)
		except Exception:
			self.logFileContents(stdouterr[1]) or self.logFileContents(stdouterr[0])
			raise
		self.assertGrep(stdouterr[1], expr='.*', contains=False, assertMessage="analytics_builder build extension should not report errors/ warnings") # should not generate any error.
		return result

	def injectCumulocityEvents(self, corr):
		"""
		Inject the Cumulocity event definitions.
		:param corrHelper: The CorrelatorHelper object.
		:return: None.
		"""
		corr.injectEPL(['Cumulocity_EventDefinitions.mon'], filedir=self.project.APAMA_HOME + "/monitors/cumulocity")
		corr.injectCDP(self.project.ANALYTICS_BUILDER_SDK + '/block-api/framework/cumulocity-forward-events.cdp')
		
	def startAnalyticsBuilderCorrelator(self, blockSourceDir=None, Xclock=True, numWorkers=4, injectBlocks = True, **kwargs):
		"""
		Start a correlator with the EPL for Analytics Builder loaded.
		:param blockSourceDir: A location of blocks to include, or a list of locations
		:param Xclock: Externally clock correlator (on by default).
		:param numWorkers: Number of workers for Analytics Builder runtime (4 by default).
		:param injectBlocks: if false, don't inject the actual block EPL (use if there are dependencies), returns blockOutput directory. Also skips applicationInitialized call.
		:param \\**kwargs: extra kwargs are passed to startCorrelator
		"""

		# Build and extract the block extension:
		if blockSourceDir == None: blockSourceDir = self.input
		if not isinstance(blockSourceDir, list):
			blockSourceDir = [blockSourceDir]
		blockOutput = self.output+'/block-output-'
		blockOutputDirs=[]
		blockSrcOutput = self.output+'/block-src-'
		for blockDir in blockSourceDir:
			blockOutput=blockSrcOutput + os.path.basename(blockDir)
			self.buildExtensionDirectory(blockDir, blockOutput)
			blockOutputDirs.append(Path(blockOutput))
		# Start the correlator:
		corr = CorrelatorHelper(self)
		arguments=kwargs.get('arguments', [])
		arguments.append(f'-DanalyticsBuilder.numWorkerThreads={numWorkers}')
		arguments.append(f'-DanalyticsBuilder.timedelay_secs=0.1')
		kwargs['arguments']=arguments
		logfile=kwargs.get('logfile', 'correlator.log')
		kwargs['logfile']=logfile
		corr.start(Xclock=Xclock, **kwargs)
		corr.logfile = logfile
		corr.injectEPL([self.project.APAMA_HOME+'/monitors/'+i+'.mon' for i in ['ScenarioService', 'data_storage/MemoryStore', 'JSONPlugin', 'AnyExtractor', 'ManagementImpl', 'Management', 'ConnectivityPluginsControl', 'ConnectivityPlugins', 'HTTPClientEvents', 'AutomaticOnApplicationInitialized', 'Functional']])
		corr.injectCDP(self.project.ANALYTICS_BUILDER_SDK+'/block-api/framework/analyticsbuilder-framework.cdp')
		self.injectCumulocityEvents(corr)
		corr.injectCDP(self.project.ANALYTICS_BUILDER_SDK + '/block-api/framework/cumulocity-inventoryLookup-events.cdp')
		corr.injectEPL(self.project.ANALYTICS_BUILDER_SDK+'/testframework/resources/TestHelpers.mon')


		for blockOutput in blockOutputDirs:
			corr.send(sorted(list(blockOutput.rglob('*.evt'))))
		self.analyticsBuilderCorrelator = corr
		corr.receive('output.evt', channels=['TestOutput'])
		corr.injectTestEventLogger(channels=['TestOutput'])

		if not injectBlocks:
			return blockOutputDirs

		self.preInjectBlock(corr)

		# inject block files:
		for blockOutput in blockOutputDirs:
			corr.injectEPL(sorted(list(blockOutput.rglob('*.mon'))))
			corr.send(sorted(list(blockOutput.rglob('*.evt'))))
		# now done
		corr.sendEventStrings('com.apama.connectivity.ApplicationInitialized()')
		corr.flush(count=10)
		return corr

	def buildExtensionDirectory(self, blockSourceDir, blockOutput):
		"""
		Build a directory of blocks to a directory to inject.

		Wrapper for calling anlytics_builder build extension and extracting the output.
		:param blockSourceDir: the block source directory
		:param blockOutput: string path to output to.
		"""
		self.runAnalyticsBuilderScript(['build', 'extension', '--input', blockSourceDir, '--output', f'{blockOutput}.zip'])
		with zipfile.ZipFile(f'{blockOutput}.zip', 'r') as zf:
				os.mkdir(blockOutput)
				zf.extractall(blockOutput)


	def preInjectBlock(self, corr):
		"""
		Inject anything required before injecting blocks.

		Tests can override this to inject/ send anything required before injecting blocks. Default implemenation is a no-op.
		:param corr:  The correlator object to use
		"""
		pass


	def createTestModel(self, blockUnderTest, parameters={}, id=None, corr=None, inputs={}, isDeviceOrGroup=None, wiring=[]):
		"""
		Create a test model.

		A test model tests a blockUnderTest and connects generic inputs and outputs to its block inputs/ outputs.
		:param blockUnderTest: Fully qualified name of the block to test (including package name).  Or a list of block fully qualified names, in which case wiring is required too.
		:param parameters: Map of identifier, value per parameter. (or if multiple models specified, block id to map of parameters)
		:param id: An identifier for the model. Uses the sequence model_0 model_1, etc. if not specified.
		:param corr: The correlator object to use - defaults to the last correlator started by startAnalyticsBuilderCorrelator.
		:param inputs: A map of input identifiers and corresponding type names. If the type name is empty, that input is not connected.
		:param isDeviceOrGroup: Cumulocity device or group identifier.
		:param if more than one block supplied, then this contains the wiring as a list of strings in the form source block index:output id:target block index:input id - e.g. ['0:timeWindow:1:window', '0:timeWindow:1:otherInput']
		:return: The identifier of the created model.
		"""
		if corr == None: corr = self.analyticsBuilderCorrelator
		if isDeviceOrGroup == None: isDeviceOrGroup = 'c8y_IsDevice'
		if id == None:
			id = 'model_%s' % self.modelId
			self.modelId = self.modelId + 1
		waiter = Waiter(self, corr)
		if not isinstance(blockUnderTest, list):
			blockUnderTest=[blockUnderTest]
		testParams=', '.join([json.dumps(blockUnderTest), json.dumps(id), json.dumps(json.dumps(parameters)), json.dumps(json.dumps(inputs)), json.dumps(wiring), '{"isDeviceOrGroup":any(string, "%s")}'%isDeviceOrGroup])
		corr.sendEventStrings(f'apamax.analyticsbuilder.test.Test({testParams})')
		waiter.waitFor(expr='com.apama.scenario.Created', errorExpr='CreateFailed')
		return id


	def sendInput(self, value=0.0, name='value', id=None, corr=None):
		"""
		Send an input to a block under test.

		:param value: The value to send. Default to 0, but can be string or boolean.
		:param name: The identifier of the input to send to.
		:param id: The model to test, or model_0 by default
		:param corr: The correlator to use, or last started by startAnalyticsBuilderCorrelator by default.
		"""
		if corr == None: corr = self.analyticsBuilderCorrelator
		self.sendEventStrings(corr, self.inputEvent(name, value, id))

	def timestamp(self, t):
		"""
		Generate a string for a pseudo-timestamp event.
		"""
		return f'&TIME({t})'

	def _toAnyType (self, value):
		""" Generate Apama 'any' representation of the given value. """
		if value is None:
			return 'any()'

		typeName = 'float'
		if isinstance(value, bool):
			typeName = 'boolean'
			value = str(value).lower()
		elif isinstance(value, int) or isinstance(value, float):
			typeName = 'float'
		elif isinstance(value, str):
			typeName = 'string'
			value = f'"{value}"'
		elif isinstance(value, list):
			typeName = 'sequence<any>'
			value = '[' + ','.join([self._toAnyType(v) for v in value]) + ']'
		elif isinstance(value, dict):
			typeName = 'dictionary<any,any>'
			value = '{' + ','.join([f'{self._toAnyType(k)}:{self._toAnyType(v)}' for (k,v) in value.items()]) + '}'
		else:
			raise Exception(f'Unexpected type of value {value}')

		return f'any({typeName},{value})'

	def inputEvent(self, name, value=0.0, id='model_0', partition='', eplType = 'string', properties=None):
		"""
		Generate the string form of an input event.
		:param name: The identifier of the input to send to.
		:param value: The value to send. Default to 0, but can be string or boolean.
		:param id: The model to test, or model_0 by default.
		:param partition: The partition to send input.
		:param properties: The Properties to send. Default is empty dictionary.
		"""
		if isinstance(value, float) or isinstance(value, int): eplType = 'float'
		if isinstance(value, bool): 
			eplType = 'boolean'
			value = str(value).lower()
		if eplType == 'string':
			value = json.dumps(value)

		if properties is None:
			properties = {}
		if not isinstance(properties, dict):
			raise Exception('The properties parameter must be a dictionary.')
		props = []
		for k,v in properties.items():
			props.append(f'"{k}":{self._toAnyType(v)}')
		properties = '{' + ','.join(props) + '}'
		return f'apamax.analyticsbuilder.test.Input("{name}","{id}","{partition}",any({eplType},{value}),{properties})'
	
	def outputFromBlock(self, outputId, modelId='model_0', partitionId=None,time=None):
		"""
		Get all of the outputs of a block
		:param outputId: The identifier of the output
		:param modelId: The model to test, or model_0 by default
		:param partitionId: which partition, or None by default to not filter by partition.
		:param time: at which time, or None by default to not filter by time.
		:return: list of the values.
		"""
		return [evt['value'] for evt in self.apama.extractEventLoggerOutput(self.analyticsBuilderCorrelator.logfile)
			if evt['modelId'] == modelId and evt['outputId'] == outputId and (partitionId == None or evt['partitionId'] == partitionId ) and (time == None or evt['time'] == time )]

	def allOutputFromBlock(self, modelId='model_0'):
		"""
		Get all of the outputs of a block - a list of dictionaries
		:param modelId: The model to test, or model_0 by default
		:return: list of dictionaries with keys including value, partitionId, time, outputId, modelId and properties
		"""
		return [evt for evt in self.apama.extractEventLoggerOutput(self.analyticsBuilderCorrelator.logfile)
			if evt['modelId'] == modelId]

	def assertBlockOutput(self, outputId, expected, modelId='model_0', partitionId = None, time=None ,**kwargs):
		self.assertThat('output == expected', output=self.outputFromBlock(outputId, modelId = modelId, partitionId = partitionId,time=time), expected=expected, **kwargs)

	def outputExpr(self, name='.*', value=None, id='.*', partition='.*', time='.*', properties='.*'):
		"""
		Expression for assertGrep for an output event to look for.
		Deprecated: use assertBlockOutput, outputFromBlock or allOutputFromBlock
		:param name: The identifier of the output
		:param value: The value to look for
		:param id: The model to test, or model_0 by default
		"""
		open=''
		end=''
		if isinstance(value, str):
			value=json.dumps(value)
		if value == None:
			value = '.*'
		if isinstance(value, float):
			value = self.formatFloat(value)

		return f'apamax.analyticsbuilder.test.Output\\("{name}","{id}","{partition}",{time},any\\(.*,{value}\\),{open}{properties}{end}\\)'

	def sendEventStrings(self, corr, *events, **kwargs):
		"""
		Send events to the correlator.

		This method will include flushing the events.
		"""
		events = list(events)
		events.insert(0, '&FLUSHING(50)')
		corr.sendEventStrings(*events, **kwargs)

	def checkLogs(self, logfile=None):
		"""
		Check the correlator log files for errors/warnings.

		Verify the log files do not contain any errors. Don't use if you have tested with invalid parameters.
		:param logFile: Name of the log file, or uses last correlator started by startAnalyticsBuilderCorrelator by default.
		"""
		if logfile == None:
			logfile = self.analyticsBuilderCorrelator.logfile
		self.assertGrep(logfile, expr=' ERROR .*', contains=False)
		self.assertGrep(logfile, expr=' WARN .*', contains=False, ignores=['RLIMIT.* is not unlimited'])

	def formatFloatExponent(self, num):
		e = math.floor(math.log10(abs(num)))
		normalized = num * math.pow(10, -e)
		return f'{self.formatFloatSimple(normalized)}e{e:+03}'

	def formatFloatSimple(self, num):
		# always in straightforward non-exponent form:
		parts = list(map(lambda x: '' if int(x) == 0 else x, f'{num}'.split('.')))
		if (len(parts) == 1 or parts[1] == ''): return f'{parts[0]}'
		return f'{parts[0]}.{parts[1]}'

	def formatFloat(self, num):
		"""
		Normalises decimal number to match what Apama does

		This will be used for verifying output expression.
		:param num: the float value passed to outputExpr in test
		:return:
		"""
		if not math.isfinite(num):  # Infinite, NaN
			if num == math.inf: return 'Infinity'
			if num == -math.inf: return '-Infinity'
			return 'NaN'  # note: NaN != NaN
		if (num == 0): return '0'
		e = math.floor(math.log10(abs(num)))
		normalized = num * math.pow(10, -e)
		if (e < -4):
			return self.formatFloatExponent(num)
		if (e < 7):
			return self.formatFloatSimple(num)
		if (e < 16):
			simple = self.formatFloatSimple(num)
			# use exponent form iff shorter:
			if len(str(normalized)) + 4 < len(simple):
				return self.formatFloatExponent(num)
			else:
				return simple
		return self.formatFloatExponent(num)
