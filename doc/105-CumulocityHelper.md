# Cumulocity-specific helpers

There are several functions specific to blocks that input or output data associated with a Cumulocity IoT device or device group. To avoid repeating this functionality, a set of helper events is provided to use in Cumulocity IoT input and output blocks.

These helper events handle the following functionality:

* Looking up the source/destination object and determining if it is a group of devices and if it is, finding all of the devices within it.
* Determining if the object is a broadcast device.
* Declaring input or output with correct partition value (see also [Partition values](070-Partitions.md)).
* Adding a list of devices used within the model to the `$modelScopeParameters`, which can then be used by other blocks.
* Handling the tagging of synchronous output events sent to Cumulocity IoT.
* Forwarding outputs to models consuming the output values.
* Reporting dropped events. 

The main event types are `CumulocityInputHandler` and `CumulocityOutputHandler`. They internally use the `InventoryLookup` event type, which returns a `Promise` of a result of looking up an object in the inventory.

If using Software AG Designer, add the bundle **Cumulocity Block helpers (Support for Cumulocity input and output blocks)**.

## Input blocks

Define a parameter of `any` type to hold the identifier of the source device from which inputs are received.

```java
/**
 * Input Source.
 *
 * Defines the device or group of devices from which the alarm has been received.
 *
 * This can be a single device, or an object that references or contains a group of devices.
 * @$semanticType c8y_deviceOrGroupId
 */
any deviceId;
```

The value of the parameter (`deviceId` in the above) will be either a `string` or a `dictionary` with an `id` entry for the selected source. Pass the value of the parameter to the `CumulocityInputParams` object, which can validate the value and determine the ID of the input source.

In the `$validate` action, create a `CumulocityInputParams` object by calling the `create` static action, providing a reference to the block object, the device identifier (the `deviceId` parameter in the above example), and the type of the Cumulocity IoT event the block is listening for. Update the `CumulocityInputParams` object to include the fields the block is filtering on by calling `withFields`, providing a dictionary describing the input stream. Then declare the input by calling the `declare` action on the `CumulocityInputParams` object, providing a callback action to receive a `CumulocityInputHandler` object for the input. This is an asynchronous operation that returns a `Promise`. The `Promise` returned from this action must be returned from the `$validate` action. The callback action is called before the returned `Promise` is fulfilled.

```Java
/**The parameters for the block. */
AlarmInput_$Parameters $parameters;

/** The input handler for scheduling input events. */
CumulocityInputHandler inputHandler;

/**
 * Validates that the device exists in the inventory.
 * See - "Asynchronous validations" in the Block SDK documentation for more details.
 */
action $validate() returns Promise {
    // Create a CumulocityInputParams object to declare that the input block consumes events of 
    // type Alarm and filter the alarms further for the type specified by the block parameter alarmType.
    CumulocityInputParams params := CumulocityInputParams
                                        .create($parameters.deviceId, self, Alarm.getName())
                                        .withFields({"type":<any>$parameters.alarmType});
    // Declare the input stream and provide the callback action to save the input handler. 
    // Return the Promise returned from the declare call.
    return params.declare(inputHandlerCreated);
}

/** Call back action to receive and save the handler object.*/
action inputHandlerCreated(CumulocityInputHandler inputHandler) {
    self.inputHandler := inputHandler;
}
```

Before calling `params.declare`, register a call back using `withLookupResultHandler` on the `CumulocityInputParams` object if any further validations are needed on inventory lookup results.

Call the `schedule` action on the `CumulocityInputHandler` object to schedule an input event to be processed at the specified time, providing the input value (this should be an event object whose type is the same as the event type specified in the `CumulocityInputParams.create` call) and the source timestamp of the value.

```Java
/**
 * Method starts listening for alarms from Cumulocity IoT.
 */
action $init() {
    string id;
    // List of devices for which input events should be listened can be accessed
    // via the getDevices() action.
    for id in inputHandler.getDevices() {
        on all Alarm(type = $parameters.alarmType, source = id) as alm {
            // If ignoreTimestamp is enabled, use an empty timestamp
            // so that the framework will calculate the next timestamp to process the event.
            optional<float> timeValue := new optional<float>;
            
            // If ignoreTimestamp is disabled, use the event time.
            if not ignoreTimestamp {
                timeValue := alm.time;
            }
            // Schedule events to be processed as per the timeValue, passing the input event
            // as payload, it will be received back in the $timerTriggered action as the $payload parameter.
            // The inputHandler is the one that got saved from the callback of
            // the CumulocityInputParams.declare action.
            TimerHandle handle := inputHandler.schedule(alm, timeValue);
        }
    }
}
```
Note: To schedule an input event to be processed as soon as possible, call the `scheduleNow` action on the `CumulocityInputHandler` object or call the `schedule` action with an empty timestamp value.

The `CumulocityInputHandler` object has actions to check if a source device is a broadcast device or is a device group, and getting all the devices specified by the source device identifier.

For an example, see the **DeviceLocationInput.mon** sample.

### Multiple inputs

For blocks consuming multiple input types, create multiple input handlers to schedule corresponding input values. See the **DualMeasurementIO.mon** sample for an example.

## Output blocks

Define a parameter of `any` type to hold the identifier of the destination device to which outputs are to be sent.

```java
/**
 * Output Destination.
 *
 * The device (or for models handling group of devices, trigger device or asset) 
 * that the alarm is associated with. Assets can be used only for sending cross-device aggregates.
 * 
 * The model editor uses the device name. This is mapped internally to the device identifier.
 * @$semanticType c8y_deviceIdOrCurrentDevice
 */
any deviceId;
```

The value of the parameter (`deviceId` in the above) will be either a `string`, a `dictionary` with an `id` entry for the selected source, or a `dictionary` with a `currentDevice` entry for the "trigger device" case. Pass the value of the parameter to the `CumulocityOutputParams` object, which can validate the value and determine the ID of the output destination.

In the `$validate` action, create a `CumulocityOutputParams` object by calling either the `forSyncEventType` or `forAsyncEventType` static action depending on if the output event is synchronous or asynchronous. Pass the device identifier (the `deviceId` parameter in the above example), a reference to the block object, the event type of the Cumulocity IoT event to output, and a dictionary describing the output stream (if the output event is synchronous). See [Input and output blocks](100-InputAndOutput.md) for more information about synchronous and asynchronous output events. Examples of synchronous output events are `Alarm`, `Event`, and `Measurement` and examples of asynchronous output events are `Operation` and `ManagedObject`. Then declare the output by calling the `declare` action on the `CumulocityOutputParams` object, providing a callback action to receive a `CumulocityOutputHandler` object for the output. This is an asynchronous operation that returns a `Promise`. The `Promise` returned from this action must be returned from the `$validate` action. The callback action is called before the returned `Promise` is fulfilled.

```Java
/** The handler object which is responsible to send actual output to a channel*/
CumulocityOutputHandler outputHandler;

/** The parameters for the block. */
CreateAlarm_$Parameters $parameters;

action $validate() returns Promise {
    // Creating an CumulocityOutputParams object
    CumulocityOutputParams params := CumulocityOutputParams.forSyncEventType($parameters.deviceId, 
                                            self, Alarm.getName(), {"type":<any>$parameters.alarmType});
    // Declare the output stream and provide callback action to save the output handler object.
    // Return the Promise returned from the declare call.
    return params.declare(handlerCreated);
}
/** Callback action to receive and save CumulocityOutputHandler object.
 * @param cumulocityOutputHandler the handler object
 */
action handlerCreated(CumulocityOutputHandler cumulocityOutputHandler) {
    outputHandler := cumulocityOutputHandler;
}
```
The block should call the `deviceToOutput` action on the output handler object to obtain the device identifier of the device to which the output should be sent for the current activation. If the device specified while creating the `CumulocityOutputParams`  object was a device group, then it returns the device from the group which caused the model execution. It returns an empty value if no output should be produced for the current activation.

To send the output event, call the `sendOutput` action of the output handler object with the output event to send and the output channel as parameters. The `sendOutput` action sends the event to the specified channel and notifies the framework about the output event for profiling purposes. If the output event is synchronous, the `sendOutput` action routes the event and tags it by adding the model name before sending it to the output channel.

```Java
/**
 * Create and send an alarm to the device.
 * @param $activation The current activation.
 * @param $input_createAlarm Creates an alarm when a signal is received.
 */
action $process(Activation $activation, boolean $input_createAlarm) {
    if $input_createAlarm {
        /* Get the current device to which the output will be sent.*/
        ifpresent outputHandler.deviceToOutput($activation) as device {
            /* Creating an event to send to cumulocity.*/
            Alarm al := Alarm("", $parameters.alarmType, device, 
                            $activation.timestamp, alarmText, "ACTIVE",
                            $parameters.alarmSeverity, 1, new dictionary<string,any>);

            // Ask the framework to send the output to the output channel.
            // If output is synchronous, then it is tagged before sending it to the channel.
            outputHandler.sendOutput(al, Alarm.CHANNEL, $activation);
        }
    }
}
```

The `CumulocityOutputHandler` object has actions to check if the output device is a broadcast device, or is a trigger device, and for getting the devices for which output is to be produced.

For an example, see the **CreateEvent.mon** sample.

### Multiple outputs

For blocks producing multiple output types, create multiple output handlers to send output. See the **DualMeasurementIO.mon** sample for an example.

## Profiling

When using the recommended `CumulocityInputHandler` and `CumulocityOutputHandler` events, profiling is taken care of by the framework. See [Input and output blocks](100-InputAndOutput.md) for more information on profiling.

[< Prev: Input and output blocks](100-InputAndOutput.md) | [Contents](000-contents.md) | [Next: Asynchronous validations >](110-AsynchronousValidations.md) 
