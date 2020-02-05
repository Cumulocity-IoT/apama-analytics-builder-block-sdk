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
		modelId_failed = self.createTestModel('apamax.analyticsbuilder.samples.TimeWindow')
		
		# Checking that the model failed to load.
		self.assertGrep('all.evt', expr="Created.*No value provided for required parameter 'Duration.*'")

		# Deploying a new model with correct parameter.
		self.modelId = self.createTestModel('apamax.analyticsbuilder.samples.TimeWindow', {'durationSecs':10.0})
		
		self.sendEventStrings(correlator,
		                      self.timestamp(1.9),
		                      self.inputEvent('value', 1, id = self.modelId),
		                      self.timestamp(3))
		
		# No output yet:
		self.assertGrep('output.evt', expr=self.outputExpr('windowContents'), contains=False)
		
		self.sendEventStrings(correlator,
		                      self.timestamp(5.9),
		                      self.inputEvent('value', 2, id = self.modelId),
		                      self.timestamp(6.9),
		                      self.inputEvent('value', 3, id = self.modelId),
		                      self.timestamp(7.9),
		                      self.inputEvent('value', 4, id = self.modelId),
		                      self.timestamp(11.9),
							  self.inputEvent('value', 5, id = self.modelId),
		                      self.timestamp(14.9),
							  self.inputEvent('value', 6, id = self.modelId),
		                      self.timestamp(22),
							  self.inputEvent('reset', True, id = self.modelId),
							  self.timestamp(23.4),
							  self.inputEvent('value', 7, id = self.modelId),
							  self.timestamp(34),
							  )

	def validate(self):

		# As it's been 2 seconds since we sent the input, now the output should be generated.
		self.assertGrep('output.evt', expr=self.outputExpr('windowContents', properties='.*"timeWindow":.*WindowContents.any.float,1.,1.,.*WindowContents.any.float,2.,5.,.*WindowContents.any.float,3.,6.,.*WindowContents.any.float,4.,7.*'), contains=True)
		
		self.assertGrep('output.evt', expr=self.outputExpr('windowContents', properties='.*"timeWindow":.*WindowContents.any.float,4.,9.,.*WindowContents.any.float,5.,11.,.*WindowContents.any.float,6.,14.*'), contains=True)
		self.assertGrep('output.evt', expr=self.outputExpr('windowContents', properties='.*"timeWindow":.*WindowContents.any.float,4.,9.,.*WindowContents.any.float,5.,11.,.*WindowContents.any.float,6.,14.*'), contains=True)
		self.assertGrep('output.evt', expr=self.outputExpr('windowContents', properties='.*"timeWindow":.*WindowContents.any.float,7.,22.*'))
		self.assertGrep('output.evt', expr=self.outputExpr('windowContents', properties='.*sequence.apamax.analyticsbuilder.samples.WindowContents.*apamax.analyticsbuilder.samples.WindowContents.*apamax.analyticsbuilder.samples.WindowContents'), contains=False) # verify only one windowContents object in the output.
		
