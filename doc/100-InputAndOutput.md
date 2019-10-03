# Input and output blocks

## Input blocks

### Timestamp handling

An input block is a block that receives data from an external (to the model) source, and makes it available to other blocks within the model. An input block will typically have block *outputs* only, though it is permitted to have block inputs. All model evaluations involving sending data between blocks must happen at a specified point in time. Input blocks may take a timestamp from an external source (typically indicating exactly when the input occurred), or may treat the data as having occurred in the near future. As described in the Analytics Builder documentation, the runtime has a global configuration setting `timedelay_secs` which is the delay that the runtime will wait for before processing events. (This allows it to receive events out of order, and it will execute based on timestamp order - provided events are received within this `timedelay_secs` period).

Typically, an input block will listen for events using an `on all <EventType>` listener, started in the `$init` action. On matching an event, the block will extract a timestamp from the event, and create a timer for that value, for the appropriate [partition value](070-Partitions.md). Input blocks must use an absolute, not a relative timer. On the timer being triggered, the value from the event is sent as an output. Typically, the event received will be passed as the payload of the timer. If an event is received with a timestamp that is too old, then the `createTimerWith` will throw (this would be in effect requesting a timer trigger in the past, and that is not permitted, as it would result in having to re-evaluate a past model evaluation, and could invalidate previous outputs). If the event is too old, this should be reported to the runtime using the `BlockBase.droppedEvent` action, providing the event and the source timestamp of that event.

If a block cannot obtain a timestamp, or is configured to ignore the timestamps, it should use an absolute timer set to a time shortly in the future. This can be achieved using `BlockBase.getModelTime().nextAfter(float.INFINITY)`.

### Declaring input streams

An input block also needs to declare what event types and fields that identify a series of events (that is, what fields it is filtering on) it is consuming. This is done by calling `BlockBase.listensForInput`, providing the event type name (fully qualified, that is, including the package name), a set of field names and values it is filtering on, and which partition value it is listening for. This is required so that the runtime can determine whether an input block is receiving output from a different model, in which case the models need to be executed in the correct order.

The `fields` provided to `listensForInput` do not have to reflect exact fields of an event type. For example, when listening to Cumulocity `Measurement` objects, a `fragment` and `series` are specified, but these do not correspond to fields of an event type (instead, the values are keys in the measurements dictionary and sub-dictionary).

The `BlockBase.listensForInput` should be called during a call to `$validate`. The runtime needs to validate that any inputs or outputs for a model are legal in the context of other models running.

### Multiple inputs

For blocks that use multiple inputs, `BlockBase.listensForInput` returns an input identifier that can be added to a `TimerParams` with the `withInputId` method. This allows the framework to identify which input a block is using, and is required if the block has more than one input. This can be stored on the block object itself.

### Routing inputs to workers and partitions

As models execute in potentially multiple worker threads, each event type should be forwarded to worker contexts appropriately.

For the Cumulocity event types `Alarm`, `Event`, `Measurement` and `Operation`, a monitor included in Analytics Builder (**ForwardCumulocityMeasurements.mon**) is responsible for forwarding these to the appropriate worker context. This also identifies source managed objects with a property named `pas_broadcastDevice` and will treat these as broadcast devices; the Cumulocity input blocks will identify managed objects with this property and use the `Partition_Broadcast` partition value for these sources.

For other event types, the `RequestForwarding.byKey` or `RequestForwarding.unpartitioned` actions can be called from the `$preSpawnInit` action to request forwarding of a given type. (Multiple requests for the same type are permitted, but should be consistent on which field the type is partitioned by, or if it is unpartitioned.)

For an example, see the **DeviceLocationInput.mon** sample.

## Output blocks

An output block is a block that sends data to an external target. An output block will typically have block *inputs* only (the value to send), but it may have block outputs as well.

Output blocks should construct the event to send, typically using block inputs and parameters. The event should be routed (using the `route` statement) and sent (using the `send` statement) to the appropriate channel. The event is routed so that other models can pick up the same event and process it.

When sending events, these may be sent to an external system that will or will not echo the same event back to the correlator. For example, sending an HTTP request to a remote web service would result in a response, but the request would not be sent to the correlator. However, invoking a web service hosted by the correlator itself or sending to a system such as Cumulocity IoT or a message bus which echoes events back to the correlator would result in the correlator receiving the event again. In these cases, output blocks should make a distinction between the event routed and the one sent (which will be echoed back to the correlator). For Cumulocity `Measurement` objects, this is achieved by adding a property identifying the model name to the event sent to Cumulocity, but not the event routed internally. The input block ignores events with this property set; it should have already processed them (and they are likely to be treated as "late").

An output block also needs to declare what event types and fields it is sending and whether the generated output is time synchronous or asynchronous. If the output is time synchronous, then this is done by calling `BlockBase.sendsSyncOutput` with the same parameters as an input block would use, else call `BlockBase.sendsAsyncOutput`.

## Profiling

To aid the framework in profiling (providing a count of block inputs and outputs), blocks should call the action `$base.profile(BlockBase.PROFILE_OUTPUT)` when an event is sent from a model. Similarly, on a dropped event (as the timestamp is too old), call `$base.droppedEvent(<evt>, <time>)` where `<evt>` is the event object which will be dropped and `<time>` is the time (in seconds since the Unix epoch). This will update the count of dropped events and forward the event to the `DroppedEvent.CHANNEL`. An EPL monitor can receive these events to report the dropped events.

## Semantic types

For input and output blocks that have a parameter that refers to a Cumulocity device or device group, a block can declare that the parameter is selecting a Cumulocity device identifier by adding an ApamaDoc `@$semantictype` tag. Values following the tag can be:

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

**Note:** Avoid using common id with different type between two input or two output blocks.

[< Prev: The Value type](090-ValueType.md) | [Contents](000-contents.md) | [Next: Cumulocity-specific helpers >](105-CumulocityHelper.md) 
