# Partition values

All model evaluation must occur in the context of a partition. For a model processing events from multiple devices in a group, the partition corresponds to each device within the group. For models processing events from a single device, the model will have a single partition.

A timer may be created from within a `$process` call or a `$timerTriggered` call as part of model evaluation. In these cases, by default the partition for the timer will be inherited from the executing context. For an example, see the **TimeDelay.mon** sample which just uses the simple `$base.createTimer` method; the partition is implicitly the same as that which triggered the block's execution.

A timer may also be created from the `$init` action, or from a listener set up in the `$init` action. In this case, there is no partition associated with the execution of the `$init` action, so a partition value should be provided in a `TimerParams` object.

Partition values can be used in timers or when a block declares an external [input or output](100-InputAndOutput.md). The value can be one of the following:

| Name | Valid for use in timers | Valid for declaring input or output | Description |
|------|-----|-----|--------------------------------|
| `Partition_Alias`     | N | Y | Denotes an "alias" device. This is used in simulation mode and test mode to declare the real and virtual devices. In terms of checking for cycles and what model-to-model interactions are used, the `realDevice` member is used, but the block actually listens to events identified by the `virtualDevice` field. |
| `Partition_Broadcast` | Y | N | The timer will execute for every partition that the model is active for. |
| `Partition_Default`   | N | Y | Denotes a default partition. This is used if the model is not using independent execution for different partitions. In the Cumulocity input blocks, this is used if they are configured with a normal device. |
| `Partition_Wildcard`  | N | Y | A block input or output applies to multiple partition values (for example, used for inputs/outputs configured with device groups). |
| Any other type (for example, a string or integer value) | Y | Y | An identifier for a distinct partition. For example, in Cumulocity input blocks configured with a device group, the individual member device identifier (a string value) is used for the per-device partition. |

For normal value partitions, it is only legal to create a timer with that partition in the worker context that is associated with that partition. These are typically created from listeners from events, which the framework's forwarding monitor will send to the appropriate context.

For examples, see the **ManagedObjectInput.mon** sample.

[< Prev: Timers](060-Timers.md) | [Contents](000-contents.md) | [Next: Dynamic types >](080-DynamicTypes.md) 
