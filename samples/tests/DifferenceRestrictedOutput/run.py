#
#  Copyright (c) 2019-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
#   This file is licensed under the Apache 2.0 license - see https://www.apache.org/licenses/LICENSE-2.0
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest

class PySysTest(AnalyticsBuilderBaseTest):
	def execute(self):
		self.correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		
		self.modelId = self.createTestModel('apamax.analyticsbuilder.samples.Difference', outputs={'signedDifference': None})
		
		self.sendEventStrings(self.correlator,
							  self.timestamp(1),
							  self.inputEvent('value1', 12.25, id = self.modelId),
							  self.timestamp(2),
							  self.inputEvent('value2', 7.75, id = self.modelId),  #absolute Output at this point would be 4.5 (12.25-7.75)
							  self.timestamp(2.1),
							  self.inputEvent('value2', 17.25, id=self.modelId),  #signed Output at this point would be -5 (12.25-17.25)
							  self.timestamp(2.5),
							  )


	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs()
		
		# Verifying that the model is deployed successfully.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"' + self.modelId + '\" with PRODUCTION mode has started')
		
		# Verifying the result - output from the block.
		self.assertBlockOutput('absoluteDifference', [4.5, 5])
		self.assertThat('output == empty', output=self.outputFromBlock('signedDifference'), empty=[])
