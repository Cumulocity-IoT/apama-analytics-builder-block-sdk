# Blocks with state

While a block can contain fields on the event type for the block, these fields should not be used to store state that changes as the model executes.  For this "runtime state", use a separate event type, named `<block>_$State`. This can be supplied as a `$blockState` parameter to the `$process` method of the block. It can contain whatever values that are required by the block to execute.

The following is an example block that produces a running sum of input values:

```Java
event Sum_$State {
    float sum;
}

event Sum {
    BlockBase $base;
    action $process(Activation $activation, float $input_value, Sum_$State $blockState) {
        $blockState.sum := $blockState.sum + $input_value;
        $setOutput_sum($activation, $blockState.sum);
    }
    action<Activation, float> $setOutput_sum;
}
```

Separating the state to a different object allows the framework to provide a different `$State` object for each partition that a model may execute, without blocks needing to manage which state belongs to which partition. A model may use multiple partitions if it is being used to process different devices within a device group in Cumulocity IoT. In this case, the framework will maintain a separate `$State` object for each partition, and provide it to blocks when they receive input.

Keeping the runtime state of a block separate from the block implementation also facilitates potential future features of Analytics Builder:

* Storing the state so it is not lost if the correlator is stopped.
* Moving processing from one correlator to another or from one context to another.
* Upgrading from old blocks to newer implementations of the blocks.

The state may contain any fields, but these fields should be serializable. This excludes the following EPL types:

* `action<..>`
* `chunk`
* `listener`
* `any` values of the above
* any value such as an event that includes a value of one of the above types within it

This restriction to serializable-only values is not currently enforced.

Refer to the **Windowing.mon** sample for an example of a block that uses state.

[< Prev: Parameters, block startup and error handling](040-Parameters.md) | [Contents](000-contents.md) | [Next: Timers >](060-Timers.md) 
