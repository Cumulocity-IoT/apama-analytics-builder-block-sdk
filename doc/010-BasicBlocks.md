# Basic blocks

Blocks are written in EPL as event definitions, with actions. A block must at a minimum have the following (we will assume blocks will have at least one input or output):

* A field named `$base` of type `apama.analyticsbuilder.BlockBase`.
* If it has inputs, a `$process` action. The parameters for this will typically include:

  * `Activation $activation` - this is contextual information required when generating a block output. Blocks should only use the `Activation` object passed to them from the framework, never creating their own or holding on to an `Activation` object.
  * `<type> $input_<name>` - for example, `float $input_value` for each input node the block receives from other blocks in the model.

* If it has outputs, an `action<Activation,<type> > $setOutput_<name>` (for example, `action<Activation, float> $setOutput_output`) field. This is a field of the event, like values such as string, but the type is a callable action. The block should call this, typically from the `$process` action, when it has generated a new output.

(Typically, types from another package would have a corresponding `using` statement so that they can be referred to by their short name).

For most blocks, the `$process` action is where the main processing of the block will take place, based on the input values provided.

Thus, a very simple block implementation could be:

```Java
package apamax.sampleblock;
using apama.analyticsbuilder.BlockBase;
using apama.analyticsbuilder.Activation;

/**
 * @$blockCategory Calculations
 */
event Offset {
    BlockBase $base;
    action $process(Activation $activation, float $input_value) {
        $setOutput_output($activation, $input_value + 100.0 );
    }
    action<Activation, float> $setOutput_output;
}
```
> **Hints:**
> - A block must be defined inside a package.
> - Setting the `@$blockCategory` ApamaDoc tag is mandatory.  For more information, see [Naming and Documenting Blocks](020-NamingAndDoc.md).


This block simply adds 100 to every input value. The `$process` action has parameters for the inputs, and the output is sent by calling the `$setOutput_output` action field. The framework takes care of creating an instance of the block when it is required for a model, initializing the `$base` and `$setOutput_output` fields and calling the `$process` action when the block receives input.

The type signature of the `$process` action is not fixed. If a block has more inputs, it can include more `$input_`-prefixed parameters. The types of the `$input_` parameters indicate the types of the inputs (see also [dynamic types](080-DynamicTypes.md)). The framework inspects the type of the `$process` action (and indeed, whether the block even has one) and will call it accordingly. As we will see later, there are other parameters that can be included in a `$process` signature. The framework uses a form of "Dependency injection" when creating the block and calling the `$process` action (and others). This means that blocks only need to mention the parameters they require, not the full set of features provided by the Analytics Builder framework.

The existence of a `$process` action denotes that the block has inputs, and the identifiers of the block's inputs are the parameter names starting with `$input_` with the prefix removed. Thus, the above block has an input with an identifier `value` (and of type `float`). The existence of a `$setOutput_output` denotes that the block has an output with an identifier `output` (and of type `float`). A more complex block could have multiple inputs (extra parameters to the `$process` action), or more outputs - more `$setOutput_`-prefixed action type fields.

Inputs and outputs can be one of the following types:

* `float`
* `string`
* `boolean` \(used for both `boolean` and `pulse` wire types - see [later](080-DynamicTypes.md) and the Streaming Analytics documentation topic "The pulse type" for the difference between `boolean` and `pulse` types\)
* `any`
* `Value`

Refer to a [later](090-ValueType.md) chapter for the `any` and `Value` types.

If a block has multiple inputs, it may be that only some are connected, or only some inputs have received values when the block is first called. If basic types such as `float` or `string` are used, then the `$input` parameters will be provided with their default value when `$process` is called. It is recommended that any blocks with more than one input use `optional<type>` as the type of the `$input` parameters; the block can then distinguish between an input where a value has been provided or not. For example, the `$process` action of the **Difference** block only generates an output if both inputs have received a value (do not treat `0` as not having received a value - `0` may be a valid actual input value):

```Java
action $process(Activation $activation, optional<float> $input_value1, optional<float> $input_value2) {
    ifpresent $input_value1, $input_value2{
        float result :=  $input_value1-$input_value2;
        $setOutput_absoluteDifference($activation, result.abs());
        $setOutput_signedDifference($activation, result);
    }
}
```

Where a block has multiple inputs, the framework will normally provide the latest value on each input to the `$process` action. Blocks do not need to cache the latest value. The exception to this rule are inputs of the `pulse` type, which are automatically reset to `false` values.

Blocks can also call methods on the `$base` field, which can provide contextual information about the model the block is within, including:

* `getBlockId()` - to get a unique identifier of the block within the model, for example, for debugging.
* `getInputCount(input)` - to get the count of connections to a specified input identifier. This will currently return 0 or 1.
* `getInputTypeName(input)` - to get the type of the wire attached to the input (useful for the `any` and `Value` types on inputs).

[< Prev: Using Apama Plugin for Eclipse](007-UsingDesigner.md) | [Contents](000-contents.md) | [Next: Naming and documenting blocks >](020-NamingAndDoc.md) 
