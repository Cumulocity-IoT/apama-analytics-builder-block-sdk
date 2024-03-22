# Timers

Timers can be used by processing blocks (for example, the **Delay** block) to execute something later. They are also used by input blocks. Timers must be managed by the Analytics Builder framework. This allows the runtime to handle:

* Models executing in simulation mode, which run at some offset from real time.
* Multiple timers firing at the same time from different blocks executing a single model "activation".

To create a timer, use the `BlockBase` methods `createTimer` and `createTimerWith`. The `createTimer` takes a relative offset time and a `payload`. The `createTimerWith` allows passing a `TimerParams` object to give more control.

Blocks should not use the `currentTime` variable to get the current model time. The current model time depends on the duration of the reorder buffer used by the input blocks. If required, the current model time can be obtained from the `timestamp` field of the `Activation` object which is passed as a parameter to the `$process` and `$timerTriggered` actions.

When the timer fires, it will call a method named `$timerTriggered` on the block. This can take parameters including:

* `Activation $activation`
* Block `$State` `$blockState`
* `$payload` (of any EPL type - `string`, `float`, event types, `any`, etc.)
* `$input_value` (subset of inputs of the block.)
* `TimerHandle $timerHandle`
* `ConfigPropertyValue $configPropertyValues`

From this `$timerTriggered`, it is thus possible to call the `$setOutput` actions with the provided `$activation` value.

The `$payload` is the value provided to `createTimer` or added to the `TimerParams`. If the `$payload` is not provided, the value of the `$payload` will be the empty.

The `$input_value` is one of the inputs of the block. When the timer triggers and the `$timerTriggered` action is called, `$input_value` will have the latest value that the block received and not the value when the timer was created.

The following is a simple example of timers, to delay float values by 1 second:

```Java
event Delay1Sec {
    BlockBase $base;
    action $process(float $input_value) {
        $base.createTimerWith(TimerParams.relative(1.0).withPayload($input_value));
    }
    action $timerTriggered(Activation $activation, any $payload) {
        $setOutput_delayed($activation,<float>$payload);
    }
    action<Activation, float> $setOutput_delayed;
}
```

## Timer handles

The `createTimerWith` action returns a `TimerHandle` object (and this can also be a parameter to the `$timerTriggered` action). This allows the timer to be canceled by calling `$base.cancelTimer(timerHandle)`. The `TimerHandle` can be stored in the `$State` object if required.

## Timer parameters

`TimerParams` allows the user to create a timer which is:

* Absolute: fires at an absolute point in time (taking into account any offset due to running in simulation mode).
* Relative: as per the `createTimer` method.
* Recurring: a recurring timer will trigger at the interval specified.

`TimerParams` allows adding a payload via the `withPayload` action, and a [partition](070-Partitions.md) can be specified.

For absolute timers, if the specified time is in the past, the Analytics Builder framework will call the `$timerRejected` method defined on the block. This method can take the following parameters: `TimerHandle $timerHandle` and `string $reason` (the reason for the timer rejection). If the method is not defined on the block, the Analytics Builder framework will throw an exception.

[< Prev: Blocks with state](050-State.md) | [Contents](000-contents.md) | [Next: Partition values >](070-Partitions.md) 
