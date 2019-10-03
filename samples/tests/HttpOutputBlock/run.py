#
#  $Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
#   This file is licensed under the Apache 2.0 license - see https://www.apache.org/licenses/LICENSE-2.0
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest

class PySysTest(AnalyticsBuilderBaseTest):
	def startPython(self, script, args, ignoreExitStatus=False, stdouterr=None, environs=None, pythonPaths=None, **kwargs):
		"""
		Starts a python process, using the same python version and environment the tests are running under (python 3)
		@param script: .py file from input dir or absolute path
		@param stdouterr: the prefix to use for std out and err files
		@param environs: additional env vars which will override those in the parent process
		@param pythonPaths: additional python paths
		"""
		script = os.path.join(self.input, script)
		assert os.path.exists(script), script
		if not stdouterr: stdouterr = os.path.basename(script)

		env = dict(os.environ)
		env['PYTHONDONTWRITEBYTECODE'] = 'true'
		if environs: env.update(environs)

		if pythonPaths:
			env['PYTHONPATH'] = os.pathsep.join(pythonPaths) + os.pathsep + env.get('PYTHONPATH', '')

		try:
			return self.startProcess(sys.executable, [script]+args,
				ignoreExitStatus=ignoreExitStatus, stdout=stdouterr+'.out', stderr=stdouterr+'.err',
				displayName='python3 '+kwargs.pop('displayName', stdouterr), environs=env, **kwargs)
		except Exception:
			self.logFileContents(stdouterr+'.err') or self.logFileContents(stdouterr+'.out')
			raise
	
	def execute(self):
		# Using available port for HTTP connection.
		self.httpConPort = self.getNextAvailableTCPPort()
		
		# Starting dummy HTTP server.
		server = self.startPython('server.py', [str(self.httpConPort)], stdouterr='test-http-server', state=BACKGROUND)
		self.waitForSocket(self.httpConPort, process=server)
		
		# Correlator configurations:
		codecsConfig = ['--config', self.project.APAMA_HOME + '/connectivity/bundles/standard-codecs.yaml',
						'--config', self.project.APAMA_HOME + '/connectivity/bundles/HTTPClientConnectivity/GenericJSON',
						]
		
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/', arguments=codecsConfig)
		
		self.host ='localhost'
		self.modelId = self.createTestModel('apamax.analyticsbuilder.samples.HTTPOutput',
											parameters={'host':self.host, 'path':'analyticsbuilder', 'port':self.httpConPort}, inputs={'value':'string'})
		
		# Values to send out from the output block.
		self.values= ['From Analytics Builder HTTP Output block', 12345]
		self.sendEventStrings(correlator,
								self.timestamp(1),
								self.inputEvent('value', self.values[0], id = self.modelId),
								self.timestamp(1.2))
		correlator.flush() # explicitly flush to ensure that the HTTP transport has received the response
		self.sendEventStrings(correlator,								
								self.timestamp(1.4))
		self.sendEventStrings(correlator,
								self.inputEvent('value', self.values[1], id = self.modelId),
								self.timestamp(2.0))
		correlator.flush() # explicitly flush to ensure that the HTTP transport has received the response
		self.sendEventStrings(correlator,
								self.timestamp(2.1),
								self.timestamp(2.2),
								self.timestamp(3.5))

		self.waitForSignal('test-http-server.out', expr='Request data: ', condition='==2')		#Wait till all events get processed.

	def validate(self):
		# Verifying that there are no errors in the log file.
		self.checkLogs()
		
		# Verifying that the block is connected to the correct host.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Connectivity chain created.*'+self.host)
		
		# Verifying that the model is deployed successfully.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"' + self.modelId + '\" with PRODUCTION mode has started')
		
		# Verifying that we received all the values that were sent in and in same order.
		self.assertOrderedGrep('test-http-server.out', exprList=list(map(str, self.values)))
		
		self.assertOrderedGrep('output.evt', exprList=list(map(lambda x: self.outputExpr('responseBody', properties='.*.any.string,"value".:.*'+str(2 * x)+'.*'), self.values)))
		