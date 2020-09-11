#
#  $Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
#   This file is licensed under the Apache 2.0 license - see https://www.apache.org/licenses/LICENSE-2.0
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest

class PySysTest(AnalyticsBuilderBaseTest):
	def execute(self):
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		
		# engine_receive process listening on all the channels.
		correlator.receive('all.evt')
		
		# This model will fail to deploy: missing a required param:
		modelId_failed = self.createTestModel('apamax.analyticsbuilder.samples.TimeDelay')
		
		# Checking that the model failed to load.
		self.assertGrep('all.evt', expr="Created.*No value provided for required parameter 'Delay .secs.'")

		# Deploying a new model with correct parameter.
		self.modelId = self.createTestModel('apamax.analyticsbuilder.samples.TimeDelay', {'delaySecs':1.9})
		
		self.sendEventStrings(correlator,
		                      self.timestamp(1),
		                      self.inputEvent('value', 12.25, id = self.modelId),
		                      self.timestamp(2))
		
		# As delay is 1.9 seconds and it's only 1 second since we sent in the input, so block should not generate the output.
		self.assertThat('12.25 not in output', output = self.outputFromBlock('delayedValue', modelId = self.modelId))
		
		# Setting the time to 3.
		self.sendEventStrings(correlator, self.timestamp(3))
		
		# As it's been 2 seconds since we sent the input, now the output should be generated.
		self.assertThat('12.25 in output', output = self.outputFromBlock('delayedValue', modelId = self.modelId))
		
		self.sendEventStrings(correlator,
		                      self.inputEvent('value', 7.75, id = self.modelId),
		                      self.timestamp(5.1))

	def validate(self):
		# Verifying that the model is deployed successfully.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"' + self.modelId + '\" with PRODUCTION mode has started')
		self.assertBlockOutput('delayedValue', [12.25, 7.75], modelId = self.modelId)
		# Do not check logs, we expect some ERRORs from trying to activate a model with no parameters for the block.
