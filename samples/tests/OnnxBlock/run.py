#  Copyright (c) 2019-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
#   This file is licensed under the Apache 2.0 license - see https://www.apache.org/licenses/LICENSE-2.0

__pysys_title__   = r""" ONNX block: To check the basic working of the block"""
__pysys_purpose__ = r""" To check that the ONNX block is able to load and execute ONNX models correctly. """

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest

class PySysTest(AnalyticsBuilderBaseTest):
	def execute(self):
		self.correlator = self.startAnalyticsBuilderCorrelator(
			blockSourceDir=f'{self.project.SOURCE}/blocks/',
			onnxModelDir=self.input
		)
		self.correlator.injectCDP(self.project.ANALYTICS_BUILDER_SDK+'/testframework/resources/analyticsbuilder-blocks.cdp')
		
		# Model to add two scalar floats.
		# inputs: 'x', 'y'. outputs: 'z'
		self.modelId_add = self.createTestModel('apama.analyticsbuilder.blocks.ONNX', {
			'onnxModelFile': 'add.onnx',
		})
		
		self.sendEventStrings(self.correlator,
								self.timestamp(1),
								self.inputEvent('inputs', True, id = self.modelId_add, properties={'x': 3, 'y': 7}),
								self.timestamp(1.2)
							)


	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs(warnIgnores=[
			r'Unable to find APPLICATION_NAME environment variable' # not set in local environment
		], errorIgnores=[
			r'Invalid type empty - should be one of string, float, boolean, Value' # this block has output type 'pulse'
		])

		# Verifying that the model is deployed successfully.
		self.assertGrep(self.correlator.logfile, expr='Model \"' + self.modelId_add + '\" with PRODUCTION mode has started')

		# Verifying model output
		add_outputs = self.allOutputFromBlock(self.modelId_add)
		self.assertThat('len(outputs) >= 1', outputs=add_outputs, message='Expected at least 1 output event from the model')
		self.assertThat("props == expected_props",
						props=add_outputs[0]['properties'],
						expected_props={'z': 10})
