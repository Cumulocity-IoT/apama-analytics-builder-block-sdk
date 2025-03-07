#
#  Copyright (c) 2020-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
#	This file is licensed under the Apache 2.0 license - see https://www.apache.org/licenses/LICENSE-2.0
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest


class PySysTest(AnalyticsBuilderBaseTest):
	def execute(self):
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		# engine_receive process listening on all the channels.
		correlator.receive('output.evt')

		# This model will fail to deploy: missing a required param:
		modelId_failed = self.createTestModel('apamax.analyticsbuilder.samples.GroupStatistics', {'windowDuration': 0.0})
		model_opPeriod_failed = self.createTestModel('apamax.analyticsbuilder.samples.GroupStatistics', {'outputPeriod': -1.0})

		# Checking that the model failed to load.
		self.assertGrep('correlator.log', expr="Error validating parameters: The value of 'Window Duration \\(secs\\)':'0' must be a finite and positive number.")
		self.assertGrep('correlator.log', expr="Error validating parameters: The value of 'Output Period \\(secs\\)':'-1' must be a finite and non-negative number.")

		# Deploying new model where value of parameter windowDuration is 10, this means that block will use window of duration 10 secs.
		# So on new incoming inputs, older values in the window which are beyond 10 seconds will start expiring.
		# Please refer to block documentation for details on how these windows are maintained and will expire.
		# As no value for Output Period (secs) is provided, it will use default value for it, which is 5.
		self.modelId = self.createTestModel('apamax.analyticsbuilder.samples.GroupStatistics', {'windowDuration': 5.0}, isDeviceOrGroup='c8y_IsDeviceGroup')

		self.sendEventStrings(correlator,
								self.timestamp(1.9),
								# input for partition 1.
								self.inputEvent('value', 1.0, id=self.modelId, partition="1"),
								self.timestamp(3),
								
								# input for partition 2.
								self.inputEvent('value', 3.0, id=self.modelId, partition="2"),

								# As default outputPeriod is 5 seconds, we will get output values after this point of time.

								# Expected Output: Mean:2, Minimum: 1, Maximum: 3, Device Count: 2.
								self.timestamp(5),
								self.inputEvent('value', 5.0, id=self.modelId, partition="3"),
								self.timestamp(7.5),

								# Expected Output: Mean:3, Minimum: 1, Maximum: 5, Device Count: 3.
								self.timestamp(10),
								self.timestamp(12.5),

								# No new inputs in this period, so block will take previous received inputs for calculation.
								# Expected Output: Minimum :1 , Maximum 5 , Mean 3.0 , stdDeviation : 1.63
								self.timestamp(15),

								self.timestamp(20),
								self.inputEvent('value', 0.0, id=self.modelId, partition="3"),
								self.inputEvent('value', 0.0, id=self.modelId, partition="2"),
								self.inputEvent('value', 0.0, id=self.modelId, partition="1"),
								self.timestamp(22.5),
								self.timestamp(25),
								self.timestamp(27.5),
								self.timestamp(30),
								# Since test is using bounded window of 10 secs, previous values will be expired
								# window will be filled with 0.
								# So, all the output values would be zero except device count which is 3.
								self.timestamp(32.5),
								self.timestamp(35),
								self.timestamp(37.5),
								self.timestamp(40)
)
		correlator.flush()

	def validate(self):
		# Verifying that the model is deployed successfully.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"' + self.modelId + '\" with PRODUCTION mode has started')

		# As GroupStatisticss block uses asynchronous operation for sharing data across workers,
		# so it might be possible that output from different partitions might not be consistent initially.
		# It would be better to check for outputs at time when data between workers would have synchronized instead of checking outputs for all timestamps.
		# That is why in this case we are checking for output at time 15.
		for partition in range(1, 4):
			time = 14.9
			self.assertBlockOutput('minValue', expected=[1.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('stdDeviation', expected=[1.632993161855452], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('meanValue', expected=[3.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('maxValue', expected=[5.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('deviceCount', expected=[3], time=time, modelId=self.modelId, partitionId='%d' % partition)

			# Check that output is 0 after previous values are expired
			time = 34.9
			self.assertBlockOutput('minValue', expected=[0.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('stdDeviation', expected=[0.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('meanValue', expected=[0.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('maxValue', expected=[0.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('deviceCount', expected=[3], time=time, modelId=self.modelId, partitionId='%d' % partition)
