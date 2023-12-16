#
#  $Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
#  Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest

class PySysTest(AnalyticsBuilderBaseTest):
	def execute(self):
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		correlator.injectEPL(self.input + '/MockedInventory.mon')
		self.model = self.createTestModel('apamax.analyticsbuilder.samples.TimeTicker', parameters={'deviceId':'group1', 'periodSecs':1}, isDeviceOrGroup='c8y_IsDeviceGroup')

		# Send time ticks so that the block generates output.
		self.sendEventStrings(correlator,
							self.timestamp(1),
							self.timestamp(2),
							self.timestamp(3),
		                    )
		
	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs()
		
		# Verifying that model is deployed successfully.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"'+self.model +'\" with PRODUCTION mode has started')
		
		# Verifying the outputs from the block.
		for device in ['1','2','3','4']:
			self.assertBlockOutput('value', [1, 2, 3], partitionId = device, modelId = self.model)
