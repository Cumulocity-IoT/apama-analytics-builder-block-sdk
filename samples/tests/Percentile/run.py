#
#  Copyright (c) 2019-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
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
		modelId_failed = self.createTestModel('apamax.analyticsbuilder.samples.Percentile', {'percentile':500.0})
		
		# Checking that the model failed to load.
		self.assertGrep('all.evt', expr="Created.*must be in the range 0 to 100 inclusive")

		# Deploying a new model with correct parameter.
		self.m5 = self.createTestModel('apamax.analyticsbuilder.samples.Percentile', {'percentile':5.0})
		self.m50 = self.createTestModel('apamax.analyticsbuilder.samples.Percentile', {'percentile':50.0})
		self.m75 = self.createTestModel('apamax.analyticsbuilder.samples.Percentile', {'percentile':75.0})
		
		# this window is 1 for 1 second, 3 for 3 seconds,  2 for 2 seconds, and 4 for 4 seconds.
		# thus, percentiles are 0-10 = 1;  10-30=2; 30-60=3; 60-100=4
		self.sendEventStrings(correlator,
		                      self.timestamp(11.9),
							 )
		for model in [self.m5, self.m50, self.m75]:
			self.sendEventStrings(correlator,
		                      self.inputEvent('window', 'apama.analyticsbuilder.Value(any(float, 10),2,{"timeWindowStartTime":any(float,2),"timeWindow":any(sequence<apamax.analyticsbuilder.samples.WindowContents>, [apamax.analyticsbuilder.samples.WindowContents(any(float,1),2), apamax.analyticsbuilder.samples.WindowContents(any(float,3),3), apamax.analyticsbuilder.samples.WindowContents(any(float,2),6), apamax.analyticsbuilder.samples.WindowContents(any(float,4),8) ])})', eplType='apama.analyticsbuilder.Value', id = model))
							  
		self.sendEventStrings(correlator,
		                      self.timestamp(14))
		

	def validate(self):

		self.assertBlockOutput('output', [1], modelId = self.m5)
		self.assertBlockOutput('output', [3], modelId = self.m50)
		self.assertBlockOutput('output', [4], modelId = self.m75)
