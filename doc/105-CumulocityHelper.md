# Cumulocity-specific helpers

There are a number of functions specific to blocks that input or output data associated with a Cumulocity device or device group. To avoid repeating this functionality, a set of helper events is provided to use in Cumulocity input and output blocks.

These helper events handle the following functionality:

* Adding a list of devices used within the model to the `$modelScopeParameters`, which can then be used by other blocks.
* Declaring the input to the framework.
* Looking up the source/target object and determining if it is a group of devices, and if it is, finding all of the devices within it.
* Determining if the object is a broadcast device.
* Declaring input or output using `PartitionAlias` (see also [Partition values](070-Partitions.md)).

The main class for this is the `InventoryLookup` event type, which returns a `Promise` of a result of looking up an object in the inventory. This can be interpreted by helper methods on the `InputHelper` and `OutputHelper` event types.

If using Software AG Designer, add the bundle **Cumulocity Block helpers (Support for Cumulocity input and output blocks)**.

## Input blocks 

For input blocks, create an `InputHelper` object by calling the `forBlock` static action, providing a reference to the block object and the `$modelScopeParameters`. Then call the `setInput` method on the `InputHelper` object, passing the device identifier, Apama event type and dictionary describing the input stream (as used in the `listensForInput` call; see also [Input and output blocks](100-InputAndOutput.md)). Then chain a call to process the result of `InventoryLookup.lookup` and return the `Promise` as follows:
```Java
InputHelper inputHelper := InputHelper.forBlock(self, $modelScopeParameters);
inputHelper.setInput(deviceId, ManagedObject.getName(), new dictionary<string, any>);

return InventoryLookup.lookup(deviceId).andThen(inputHelper.declareInput);
```

The `declareInput` method will set the following fields on the input block, if they exist:

* `sequence<string> devices` - a list of the managed object identifiers - just one if the `deviceId` is a single object, or more than one if the object is a device group.
* `boolean isGroup` - true if the input is a device group.
* `boolean isBroadcastDevice` - true if the input is a broadcast device.

This method will call an action named `throwNoDevices` on the block if there are no devices in the device group specified.

For an example, see the **DeviceLocationInput.mon** sample.

### Multiple inputs

For multiple inputs, create a `SubInput` object with a `BlockBase base` field and fields that the `InputHelper` sets, and add an instance of this for each input to the block. The `InputHelper` will use a `base` field if no `$base` field exists in the object provided to it. See the **DualMeasurementIO.mon** sample for examples.

## Output blocks

For output blocks, create an `OutputHelper` by calling the `forBlock` static action, providing a reference to the block object. Then call the `setSyncOutput` or `setAsyncOutput` method on the `OutputHelper` object, passing the device identifier, Apama event type and dictionary describing the output stream (as used by the `sendsSyncOutput` call; see also [Input and output blocks](100-InputAndOutput.md)). Then chain a call to process the result of `InventoryLookup.lookup` as follows:
```Java
OutputHelper outputHelper := OutputHelper.forBlock(self);
outputHelper.setSyncOutput(deviceId, ManagedObject.getName(), new dictionary<string, any>);

return InventoryLookup.lookup(deviceId).andThen(outputHelper.declareOutput);
```

The `declareOutput` method will set the following fields on the output block, if they exist:

* `boolean isBroadcastDevice` - true if the output is a broadcast device.

This method will call an action named `throwNoDevices` on the block if there are no devices in the device group specified.

### Multiple outputs

For multiple outputs, create a `SubOutput` object with a `BlockBase base` field and fields that the `OutputHelper` sets, and add an instance of this for each output to the block. See the **DualMeasurementIO.mon** sample for examples.

[< Prev: Input and output blocks](100-InputAndOutput.md) | [Contents](000-contents.md) | [Next: Asynchronous validations >](110-AsynchronousValidations.md) 
