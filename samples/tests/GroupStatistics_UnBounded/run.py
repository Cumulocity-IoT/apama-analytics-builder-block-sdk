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

		# Deploying new model with no parameter values for block, this means that block will use an unbounded window
		# That means on new incoming inputs, older values will not expire.
		# Also as outputPeriod parameter is not provided, it will use default value for it, which is 5.
		self.modelId = self.createTestModel('apamax.analyticsbuilder.samples.GroupStatistics', {}, isDeviceOrGroup='c8y_IsDeviceGroup')

		self.sendEventStrings(correlator,
								self.timestamp(1),
								self.inputEvent('value', 1.0, id=self.modelId, partition="1"),  # input for partition 1.

								self.timestamp(3),
								self.inputEvent('value', 3.0, id=self.modelId, partition="2"),  # input for partition 2.

								# As default outputPeriod is 5 seconds, we will get output values after this point of time.
								# and will get output for 2 partitions.

								# Expected Output: Device Count:2, Minimum: 1, Maximum: 3..
								self.timestamp(5),
								self.inputEvent('value', 5.0, id=self.modelId, partition="3"),
								self.timestamp(7.5),

								# Expected Output: Mean:2.39, Minimum: 1, Maximum: 5, Std Deviation: 1.51, Device count: 3
								self.timestamp(10),
								self.timestamp(12.5),

								# Since block is using an unbounded window, block will produce outputs from start time.
								# Expected Output: Mean:2.71, Minimum: 1, Maximum: 5, Std Deviation: 1.68, Device count: 3
								self.timestamp(15)
								)
		correlator.flush()

	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs()

		# Verifying that the model is deployed successfully.
		self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"' + self.modelId + '\" with PRODUCTION mode has started')

		# As GroupStatistics block uses asynchronous operation for sharing data across workers,
		# so it might be possible that output from different partitions might not be consistent initially.
		# It would be better to check for outputs at time when data between workers would have synchronized instead of checking outputs for all timestamps.
		# That is why in this case we are checking for output at time 15.
		for partition in range(1, 4):
			time = 14.9
			self.assertBlockOutput('minValue', expected=[1.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('stdDeviation', expected=[1.608162870331923], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('meanValue', expected=[2.7163120567375882], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('maxValue', expected=[5.0], time=time, modelId=self.modelId, partitionId='%d' % partition)
			self.assertBlockOutput('deviceCount', expected=[3], time=time, modelId=self.modelId, partitionId='%d' % partition)