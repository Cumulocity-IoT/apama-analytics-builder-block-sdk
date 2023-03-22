#
#  $Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
#   This file is licensed under the Apache 2.0 license - see https://www.apache.org/licenses/LICENSE-2.0
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest


class PySysTest(AnalyticsBuilderBaseTest):
    def execute(self):
        correlator = self.startAnalyticsBuilderCorrelator(
            blockSourceDir=f'{self.project.SOURCE}/blocks/')
        modelId = self.createTestModel('apamax.analyticsbuilder.samples.Offset')
        self.sendEventStrings(correlator,
                              self.timestamp(1),
                              self.inputEvent('value', 100.75, id=modelId),
                              self.timestamp(2),
                              self.inputEvent('value', 10.50, id=modelId),
                              self.timestamp(5),
                              )

    def validate(self):
        self.assertBlockOutput('output', [200.75, 110.50])
