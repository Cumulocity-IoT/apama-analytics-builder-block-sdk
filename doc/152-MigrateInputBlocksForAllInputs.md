# Update Cumulocity IoT input blocks to receive from all input sources

A new input source option `All Inputs` has been added for receiving inputs from all input sources. Existing Cumulocity IoT input blocks need to be updated to enable receiving from all input sources using this option.

The input block should not set up the listeners for incoming events in `$init` action. Instead, the input block should call the `createListeners()` method on the `CumulocityInputHandler` object and provide a set of field names and values as the argument to this method for filtering the events. This will then set up the listeners in `CumulocityInputHandler` and the input block will receive a callback when a matching event is received. For example, consider following block parameter `source` that can listen to all input sources.


```Java
event AlarmInput_$Parameters {
	/**
	* Input Source.
	*
	* Defines the source from which the alarm has been received.
	*
	* This can be a single device, an asset, an object that references or contains a group of devices, or all input sources.
	*
	* @$semanticType c8y_deviceOrGroupId
	*/
	any deviceId;

	...
}

event AlarmInput {

	...
	/** The input handler for scheduling input events. */
	CumulocityInputHandler inputHandler;

	/**
	* Method to set up listeners using CumulocityInputHandler and start listening for alarms from Cumulocity IoT.
	*/
	action $init(){
	
		// provide all the necessary info required to set up the listeners
		inputHandler.createListeners(Alarm.getName(), {"type" : <any>$parameters.alarmType}, handleAlarm);
	
	}

	/**
	 * Callback received from the CumulocityInputHandler when an Alarm event is received
	 * @param a The incoming Alarm event.
	 */
	action handleAlarm(any a) {

		Alarm alm := <Alarm> a;

	...
	}
}
```
The value of the parameter (deviceId in the above) will be a dictionary if the `Input Source` parameter has been set to `All Inputs`. 


[< Prev: Update Cumulocity IoT input blocks to receive from assets](151-MigrateInputBlocksForAssetInput.md) | [Contents](000-contents.md) | [Next: Sharing data across partitions and workers >](160-SharingDataAcrossPartition.md) 
