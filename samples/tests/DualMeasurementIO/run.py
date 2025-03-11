#
#  Copyright (c) 2019-present Cumulocity GmbH, Duesseldorf, Germany and/or its affiliates and/or their licensors.
#  Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Cumulocity GmbH
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest
import json

class PySysTest(AnalyticsBuilderBaseTest):
	id = 1000
	def inputMeasurement(self, source, time, type, fragments):
		"""
		Generate the string form of a Measurement event.
		:param source: Unique device identifier of the device.
		:param type: type of the measurement
		:param fragments: map of fragment to map of series to values as floats
		"""
		id = str(self.id)
		self.id = self.id+1
		fragentries=[]
		for f in fragments.keys():
			seriesentries=[]
			for s in fragments[f].keys():
				seriesentries.append(json.dumps(s)+':com.apama.cumulocity.MeasurementValue('+str(float(fragments[f][s]))+', "", {})')
			fragentries.append(json.dumps(f)+':{' + ', '.join(seriesentries) + '}')
		measurements = '{'+ ', '.join(fragentries)+'}'

				
		measurementParams = ', '.join([json.dumps(id), json.dumps(type), json.dumps(str(source)), 
									   json.dumps(time), measurements, '{}'])
		return f'"cumulocity.measurements",com.apama.cumulocity.Measurement({measurementParams})'
	
	def execute(self):
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		correlator.injectEPL(self.input + '/SendC8yObjects.mon')
		deviceId = '100'
		self.models = []
		
		modelId = self.createTestModel('apamax.analyticsbuilder.samples.DualMeasurementIO', parameters={'deviceId':deviceId}, isDeviceOrGroup='c8y_IsDevice')
		self.models.append(modelId)
		
		self.sendEventStrings(correlator,
							  self.timestamp(1),
							  self.timestamp(2.6),
							  self.timestamp(12),
							  self.inputMeasurement(deviceId, 12, 'mtype', {'numerator':{'V':12}, 'denominator':{'V':3}}),
							  self.timestamp(13),
							  self.timestamp(14),
							  self.inputMeasurement(deviceId, 14, 'mtype', {'denominator':{'V':4}}),
							  self.timestamp(15),
							  self.inputMeasurement(deviceId, 15, 'mtype', {'numerator':{'V':20}}),
							  self.timestamp(16),
							  self.inputMeasurement(deviceId, 16, 'mtype', {'numerator':{'V':18}}),
							  self.inputMeasurement(deviceId, 16, 'mtype', {'denominator':{'V':3}}),
							  self.timestamp(17),
							  self.timestamp(20))



		deviceId = '101'

		# here we create two models.  The first takes fragments X and Y as inputs and will output 'ratio' and 'inverse' measurements, and a 'ratio' block output:
		modelId = self.createTestModel('apamax.analyticsbuilder.samples.DualMeasurementIO', parameters={'deviceId':deviceId, "ratioFragment":"X", "inverseFragment":"Y"}, isDeviceOrGroup='c8y_IsDevice')
		self.models.append(modelId)
		# the second model takes numerator, denominator input, and outputs ratio as X and inverse as Y.
		modelId = self.createTestModel('apamax.analyticsbuilder.samples.DualMeasurementIO', parameters={'deviceId':deviceId, "numeratorFragment":"X", "denominatorFragment":"Y"}, isDeviceOrGroup='c8y_IsDevice')
		# thus, we have the first of these models gives X= num / den  and Y= den / num as its outputs, and the second will calculate ratio = X / Y = (num / den) / (den / num) = (num / den)^2
		self.models.append(modelId)
		self.sendEventStrings(correlator,
							  self.timestamp(21),
							  self.timestamp(22),
							  self.inputMeasurement(deviceId, 22, 'mtype', {'numerator':{'V':12}, 'denominator':{'V':3}}), # X = 4, Y= 1/4.  model2 ratio = 4 / (1/4) = 16
							  self.timestamp(23),
							  self.timestamp(25),
							  self.inputMeasurement(deviceId, 25, 'mtype', {'numerator':{'V':18}}), # den is still 3, so X = 6, Y = 1/6, ratio = 6 / (1/6) = 36
							  self.timestamp(26),
							  self.timestamp(30))


	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs()
		
		# Verifying that model is deployed successfully.
		for modelId in self.models:
			self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"'+modelId +'\" with PRODUCTION mode has started')
		self.assertBlockOutput('ratio', [4, 3, 5, 6], modelId = self.models[0])

		self.assertBlockOutput('ratio', [4, 6], modelId = self.models[1])

		self.assertBlockOutput('ratio', [16, 36], modelId = self.models[2])

