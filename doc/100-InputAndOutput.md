# Input and output blocks

> **Note:** The previous version 1 API for writing custom input and output blocks is deprecated. Input and output blocks will require changes to continue to work properly and use multiple devices in a model with the concurrency level set to more than 1. See [Migration Guide](150-MigrateInputOutputBlocks.md) for more details.

## Input blocks

An input block is a block that receives data from an external (to the model) source, and makes it available to other blocks within the model. An input block will typically have block *outputs* only, though it is permitted to have block inputs.

### Declaring input streams

An input block needs to declare what event type and fields that identify a series of events (that is, what fields it is filtering on) it is consuming. This is done by calling `BlockBase.consumesInput` from the `$validate` action by providing an `InputParams` object which returns an`InputHandler` object. Create an `InputParams` object by calling the static action `InputParams.forEventType` which returns an InputParams object back, providing the event type name (fully qualified, that is, including the package name). Then chain a call to update the InputParams object with the partition value by calling `withPartition`, providing the partition value it is listening for and calling `withFields`, providing a set of field names and values it is filtering on. This is required so that the runtime can determine whether an input block is receiving output from a different model, in which case the models need to be executed in the correct order. The InputHandler object is used to schedule input events for processing and thus should be saved for later use.

```Java
/** The input handler for scheduling input events. */
InputHandler inputHandler;

action $validate() {
        // Create an InputParams object to declare that the input block consumes events of type 
        // MyEvent, listens for the partition value specified by the block parameter `source` and 
        // filter the events further for the type specified by the block parameter `type`.
        InputParams inputParams := InputParams.forEventType(MyEvent.getName()).
                                    withPartition($parameters.source).
                                    withFields({"type":<any>$parameters.type});

        // Declaring input streams. Saved inputHandler object for scheduling input events for processing.
        inputHandler := $base.consumesInput(inputParams);
    }
```
The `fields` provided to `BlockBase.consumesInput` through the `InputParams` object do not have to reflect the exact fields of an event type but they should be consistent in fields used across all input and output blocks handling the events of the same type. For example, when listening to Cumulocity `Measurement` objects, a `fragment` and `series` are specified, but these do not correspond to fields of an event type (instead, the values are keys in the measurements dictionary and sub-dictionary).

The `BlockBase.consumesInput` action should be called during a call to `$validate`. The runtime needs to validate that any inputs or outputs for a model are legal in the context of other models running.


### Handling input events

All model evaluations involving sending data between blocks must happen at a specified point in time. Input blocks may take a timestamp from an external source (typically indicating exactly when the input occurred), or may treat the data as having occurred in the near future. As described in the Analytics Builder documentation, the runtime has a global configuration setting `timedelay_secs` which is the delay that the runtime will wait for before processing events. (This allows it to receive events out of order, and it will execute based on timestamp order - provided events are received within this `timedelay_secs` period).

Typically, an input block will listen for events using an `on all <EventType>` listener, started in the `$init` action. On matching an event, the block will extract a timestamp from the event, and create a timer for that value, for the appropriate [partition value](070-Partitions.md). Input blocks must use an absolute, not a relative timer. On the timer being triggered, the value from the event is sent as a block output. Typically, the event received will be passed as the payload of the timer. If an event is received with a timestamp that is too old, then the timer is rejected and the `$timerRejected` action is called (this would be in effect requesting a timer trigger in the past, and that is not permitted, as it would result in having to re-evaluate a past model evaluation, and could invalidate previous outputs). If the event is too old, this should be reported to the runtime using the `BlockBase.droppedEvent` action, providing the event and the source timestamp of that event.

To schedule an input event for processing at a specified time, call the `schedule` action on the `InputHandler` object by providing the input event, the source timestamp of the value and the partition to which the input value belongs. The `schedule` action creates an absolute timer for the specified timestamp with the input event as payload. If the timer is rejected because of its being too old, the input handler reports to the runtime using the `BlockBase.droppedEvent` action, providing the event and the source timestamp of that event.

If a block cannot obtain a timestamp, or is configured to ignore timestamps, it should schedule the event to a time shortly in the future. This can be done by calling the `scheduleNow` action on the `InputHandler`  or calling the `schedule` action with empty timestamp value.

```java
action $init() {
    // Listen for the events of type MyEvent and filter them by type.
    on all MyEvent(source = $parameters.source, type = $parameters.type) as e {
        // If ignoreTimestamp is enabled, use an empty timestamp
        // so that the framework will calculate the next timestamp to process the event.
        optional<float> timeValue := new optional<float>;
        
        // If ignoreTimestamp is disabled, use the event time.
        if not ignoreTimestamp {
            timeValue := e.time;
        }
        // Schedule events to be processed as per their timestamp.
        // Pass the input event as payload, it will be received back in 
        // $timerTriggered action as $payload parameter.
        TimerHandle handle := inputHandler.schedule(e, timeValue, e.source);
    }
}
```
To handle Cumulocity input events, refer to the `CumulocityInputHandler` API in [Cumulocity Helper](105-CumulocityHelper).

### Multiple inputs

For blocks that consume multiple input types, create multiple handlers and use the respective handlers to schedule input events.

### Routing inputs to workers and partitions

As models potentially execute in multiple worker threads, each event type should be forwarded to worker contexts appropriately.

For the Cumulocity event types `Alarm`, `Event`, `Measurement` and `Operation`, a monitor included in Analytics Builder (**ForwardCumulocityMeasurements.mon**) is responsible for forwarding these to the appropriate worker context. This also identifies source managed objects with a property named `pas_broadcastDevice` and will treat these as broadcast devices. The Cumulocity input blocks will identify managed objects with this property and use the `Partition_Broadcast` partition value for these sources.

For other event types, the `RequestForwarding.byKey` or `RequestForwarding.unpartitioned` actions can be called from the `$preSpawnInit` action to request forwarding of a given type. (Multiple requests for the same type are permitted, but should be consistent on which field the type is partitioned by, or if it is unpartitioned.)

For an example, see the **DeviceLocationInput.mon** sample.

## Output blocks

An output block is a block that sends data to an external target. An output block will typically have block *inputs* only (the value to send), but it may have block outputs as well.

### Declaring Output streams

An output block needs to declare what event types and fields it is sending and whether the generated output is time synchronous or asynchronous. Synchronous output values are values which have a source timestamp and can be consumed by another model in a time-synchronous manner and can be processed by the model with any other data with the same timestamp. Asynchronous output values are values which do not have a source timestamp and can only be consumed by another model in a time-asynchronous manner when they are received back from the external system.

When sending events, these may be sent to an external system that may or may not echo the same event back to the correlator. For example, sending an HTTP request to a remote web service would result in a response, but the request would not be sent to the correlator. However, invoking a web service hosted by the correlator itself or sending to a system such as Cumulocity IoT or a message bus which echoes events back to the correlator would result in the correlator receiving the event again. In these cases, input blocks should make a distinction between the event routed and the one sent (which will be echoed back to the correlator). For Cumulocity `Measurement` objects, this is achieved by adding a property identifying the model name to the event sent to Cumulocity, but not the event routed internally. The input block ignores events with this property set; it should have already processed them (and they are likely to be treated as "late").

Declaring output streams can be done by calling `BlockBase.producesOutput` from the `$validate` action which takes an `OutputParams` object as a parameter and returns an `OutputHandler` object. If the output is time synchronous, then the `OutputParams` object can be created by calling the static action `forSyncEventType` and providing the event type name, a dictionary describing the output stream, and a tagger action. The tagger action is used to tag the output event so that input blocks can recognise the echoed back events. The tagger action must have a single parameter of the output event type. If the output is time asynchronous, then the `OutputParams` object can be created by calling the static action `forAsyncEventType` and providing the event type name. The OutputHandler object is used to send output to the external source or block and thus should be saved for later use.

```Java
/** The output handler object for sending output events. */
OutputHandler outputHandler;
/* The model name to use for tagging. */
string modelName;

action $validate(dictionary<string, any> $modelScopeParameters) {
    // Extract the model name for tagging.
    modelName := $modelScopeParameters[ABConstants.MODEL_NAME_IDENTIFIER].valueToString();
    // Create an OutputParams object to declare that the output block produces time-synchronous 
    // events of type MyEvent. Also specify the partition value to which it is sending and 
    // the fields output events have.
    OutputParams params := OutputParams.forSyncEventType(MyEvent.getName(), 
                                        {"type":<any>$parameters.type}, tagOutputEvent)
                                        .withPartitionValue($parameters.source);
    // Now declare the output and save the output handler object.
    outputHandler := $base.producesOutput(params);
}

/** The callback action to add a tag to the output event.*/
action tagOutputEvent(MyEvent e) {
    // Add the model name to the ouput event so that input blocks can identify and ignore it.
    e.params[ABConstants.MODEL_NAME_IDENTIFIER] := modelName;
}


```
### Sending Output events

Output blocks should construct the event to send, typically using block inputs and parameters. The event should be routed (using the `route` statement) if synchronous and sent (using the `send` statement) to the appropriate channel. The event is routed so that other models can pick up the same event and process it.

To send the output event, call the `sendOutput` action of the output handler object with the output event to send and the output channel as parameters. The `sendOutput` action sends the event to the specified channel and notifies the framework about the output event for profiling purposes. If the output event is synchronous, the `sendOutput` action routes the event and calls the tagger action to tag the output event before sending it to the output channel.

```Java
action $process(Activation $activation, string $input_source,string $input_type) {
    /* Creating an event to send to Cumulocity IoT.*/
    MyEvent m := MyEvent($input_source, $input_type, 0.0 , new dictionary<string, any>);
    // Ask the framework to send the output to the output channel.
    // If output is synchronous, then it is tagged before sending it to the channel.
    outputHandler.sendOutput(m, MyEvent.SEND_CHANNEL, $activation);
}
```

To handle Cumulocity output events, refer to the `CumulocityOutputHandler` API in [Cumulocity Helper](105-CumulocityHelper).

### Multiple outputs

For blocks that produce multiple output types, create multiple output handlers and use the respective handlers to send output events.

## Profiling

When using the `InputHandler` and `OutputHandler` API, profiling is taken care of by the framework. The `$base.profile(BlockBase.PROFILE_OUTPUT)` action is automatically called when an `OutputHandler` is used to send an output. Similarly, on a dropped event (an event where the timestamp is too old), the `$base.droppedEvent(<evt>, <time>)` is automatically called which forwards the event to the `DroppedEvent.CHANNEL`. An EPL monitor can receive these events to report the dropped events.

## Semantic types

For input and output blocks that have a parameter that refers to a Cumulocity device or device group, a block must declare that the parameter is selecting a Cumulocity device identifier by adding an ApamaDoc `@$semantictype` tag. Values for the tag can be:

* `c8y_deviceId` - to select a single device.
* `c8y_deviceOrGroupId` - to select a device or a device group.
* `c8y_deviceIdOrCurrentDevice` - to select a single device or the special "current device" (or "trigger device").

For example:

```Java
/**
 * Device or Trigger Device.
 *
 * The device (or for models handling groups, Trigger Device) to which the operation is to be sent.
 *
 * The model editor uses the device name. This is mapped internally to the device identifier.
 * @$semanticType c8y_deviceIdOrCurrentDevice
 */
any deviceId;
```

For `c8y_deviceOrCurrentDevice`, the parameter (`deviceId` in the above) should be of the `any` type and will be either a `string` for a device or a dictionary with a `currentDevice` entry for the "current device" case.

Input and output blocks that are handling a Cumulocity device or device group, must declare the type of the block by adding an ApamaDoc `@$blockType` tag. Values for the tag can be:

* `c8y_Input` - receives data from a Cumulocity device or device group.
* `c8y_Output` - sends data to a Cumulocity device.

For example:
```Java
/**
 * Device or Device Group Location Input.
 *
 * Receives <tt>ManagedObject</tt> events from Cumulocity and extracts device location information.
 *
 * @$blockCategory Input
 * @$blockType c8y_Input
 */
event DeviceLocationInput {
    ...
}
```

**Note:** A block that receives data from an external source and also sends data to an external source must not be tagged with either `c8y_Input` or `c8y_Output`. Test mode deployment is not supported for a model which contains such blocks.

**Note:** Avoid using a common id with different type between two input or two output blocks.



[< Prev: The Value type](090-ValueType.md) | [Contents](000-contents.md) | [Next: Cumulocity-specific helpers >](105-CumulocityHelper.md) 
