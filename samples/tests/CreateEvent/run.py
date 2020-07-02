#
#  $Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.$
#  Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG
#

from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest
import json,zipfile,os
from pathlib import Path

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
		# Start Correlator and extract blocks n=and inject to correlator.
		correlator = self.startAnalyticsBuilderCorrelator(blockSourceDir=f'{self.project.SOURCE}/blocks/')
		
		# correlator.receive('c8y.evt', channels=['CumulocityIoTGenericChain'])
		# Inject custom monitor to correlator.
		correlator.injectEPL(self.input + '/SendC8yObjects.mon')
		
		# Set device ID
		deviceId = '100'
		
		#Create a test model which has both input and output blocks
		modelId = self.createTestModel(['apamax.analyticsbuilder.samples.DeviceLocationInput','apamax.analyticsbuilder.samples.CreateEvent'], 
						parameters={
							'0:deviceId':deviceId,
							"1:deviceId":deviceId, 
							"1:eventType":"c8y_Event",
							"1:eventText":"LocationFound"
						}, 
		wiring=['0:location:1:createEvent']
		, isDeviceOrGroup='c8y_IsDevice'
		)
		
		# Send managedObjects to DeviceLocationInput block and expect it to be create an Event
		self.sendEventStrings(correlator,
							self.timestamp(1),
							self.timestamp(2.6),
							self.inputManagedObject(deviceId, 'com_test_device_100' ,'Device_100',[],[],[],[],[],[],
													{'alt':93.5,'lat':17.426479,'lng':78.33123},{'c8y_IsDevice':{}}),
							self.timestamp(3),
							self.timestamp(4))
		
		correlator.flush()
		
	def validate(self):
		# Verifying that there are no errors in log file.
		self.checkLogs()
		
		#Verify CreateEvent Output block creates an event
		self.assertGrep("correlator.log",expr='Received Event: com.apama.cumulocity.Event\(.*,"c8y_Event".*LocationFound')