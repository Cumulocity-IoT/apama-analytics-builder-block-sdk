#
#  $Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
#  Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest
import json

class PySysTest(AnalyticsBuilderBaseTest):
	def inputManagedObject(self, id, type, name, supportedOperations=[], supportedMeasurements=[], childDeviceIds=[], childAssetIds=[],deviceParentIds=[], assetParentIds=[], position={}, params={}):
		"""
		Generate the string form of a managed object event.
		:param id: Unique device identifier of the device.
		:param name: Name of the device.
		:param supportedOperations: A list of supported operations for this device.
		:param supportedMeasurements: A list of supported measurements for this device.
		:param childDeviceIds: The identifiers of the child devices.
		:param childAssetIds: The identifiers of the child assets.
		:param deviceParentIds: The identifiers of the parent devices.
		:param assetParentIds: The identifiers of the parent assets.
		:param position: Contains 'lat', 'lng', 'altitude' and 'accuracy'.
		:param params: Other fragments for the managed object.
		"""
		managedObjectParams = ', '.join([json.dumps(id), json.dumps(type), json.dumps(name), json.dumps(supportedOperations), json.dumps(supportedMeasurements),
								json.dumps(childDeviceIds), json.dumps(childAssetIds), json.dumps(deviceParentIds),
								json.dumps(assetParentIds),
								json.dumps(json.dumps(position)),
								json.dumps(json.dumps(params))])
		return f'apamax.analyticsbuilder.test.SendManagedObject({managedObjectParams})'
	
	def execute(self):
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		correlator.injectEPL(self.input + '/SendC8yObjects.mon')
		deviceId = '100'
		self.models = []
		
		modelId = self.createTestModel('apamax.analyticsbuilder.samples.DeviceLocationInput', parameters={'deviceId':deviceId}, isDeviceOrGroup='c8y_IsDevice')
		self.models.append(modelId)
		
		self.sendEventStrings(correlator,
							self.timestamp(1),
							self.timestamp(2.6),
							self.inputManagedObject(deviceId, 'com_test_device_100' ,'Device_100',[],[],[],[],[],[],
													{'alt':93.5,'lat':17.426479,'lng':78.33123},{'c8y_IsDevice':{}}),
							self.timestamp(3),
							self.timestamp(4))
		
		#Creating model with a group. This group has two devices with ids '1' and '2'.
		groupId='group1'
		sub_groupDeviceIds=['1', '2']
		modelId = self.createTestModel('apamax.analyticsbuilder.samples.DeviceLocationInput', parameters={'deviceId': groupId}, isDeviceOrGroup='c8y_IsDeviceGroup')
		self.models.append(modelId)
		
		self.sendEventStrings(correlator,
								self.timestamp(10),
								self.timestamp(12),
								self.inputManagedObject(sub_groupDeviceIds[0], 'com_test_device_1', 'Device_1', [], [], [], [], [], [],
													  {'alt': 98.4, 'lat': 3.1428, 'lng': 6.2857},
													  {'c8y_IsDevice': {}}),
								self.timestamp(13),
								self.timestamp(14),
								self.inputManagedObject(sub_groupDeviceIds[1], 'com_test_device_2', 'Device_2', [], [], [],
													  [], [], [],
													  {'alt': 94.4, 'lat': 2.7182, 'lng': 0.3678},
													  {'c8y_IsDevice': {}}),
								self.timestamp(15),
								self.timestamp(20))

	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs()
		
		# Verifying that model is deployed successfully.
		for modelId in self.models:
			self.assertGrep(self.analyticsBuilderCorrelator.logfile, expr='Model \"'+modelId +'\" with PRODUCTION mode has started')
		
		# Verifying the outputs from the block.
		self.assertGrep('output.evt', expr=self.outputExpr('location', properties='.*"alt":any.float,93.5.*,"lat":any.float,17.426479.,"lng":any.float,78.33123.*', id=self.models[0]))
		self.assertGrep('output.evt', expr=self.outputExpr('location', properties='.*"alt":any.float,98.4.*,"lat":any.float,3.1428.,"lng":any.float,6.2857.*', id=self.models[1]))
		self.assertGrep('output.evt', expr=self.outputExpr('location', properties='.*"alt":any.float,94.4.*,"lat":any.float,2.7182.,"lng":any.float,.3678.*', id=self.models[1]))
