# Dynamic types

Blocks may use one of the following static types for inputs and outputs:

* `string`
* `boolean`
* `float`

Blocks may also support different types for inputs and outputs. The exact type for outputs should be provided by the block, possibly as a result of parameters or what inputs it has connected to it. Blocks can support different input types and inspect these; in which case, an `any` or `Value` type can be used as the `$process` parameter's type. What types of inputs are connected to a block are available from `BlockBase.getInputTypeName` when the `$validate` method is called. The `$validate` should throw an exception if the input types connected are incorrect.

## Providing input types

Blocks typically declare what type an input is by specifying the parameter type of the `$input_<name>` parameter of the `$process` action, including the `any` type.  However, as `boolean` is used for both `boolean` and `pulse` types, a block may also have a `string constant $INPUT_TYPE_<inputId>` constant which can be the value "string". 

## Providing output types

Blocks can declare what type an output is in the following ways:

* parameter type of the `$setOutput` action
* a `string constant $OUTPUT_TYPE_<outputId>`
* an action `$outputType_<outputId>() returns string`

At most, one of the string constant or action may be present on a block.

The string constant form, or the return value of the `$outputType` action, can be one of:

* `boolean`, `string`, `float`.
* `pulse` (to distinguish between boolean and pulse outputs).
* `input(<inputId>)` - the same type as the named input.
* `sameAsAll(<inputId1>, <inputId2>, ...)` - the same type as the named input. If any of the named input types are different, then this is treated as a validation error.
* `pulseOrBoolean(<inputId1>, <inputId2>, ...)` - if all of the named inputs are boolean, then the output type is boolean. If any of the inputs are a pulse type, then the output is a pulse type.

The `$setOutput` parameter type should be compatible with what types the block will generate. For `pulseOrBoolean`, a boolean is sufficient; in other cases, a `Value` or `any` type should be used.

For example, the following block performs an "add" operation on float or string types, but not on a mixture:

```Java
event Add {
    BlockBase $base;
    action $process(Activation $activation, any $input_value1, any $input_value2) {
        switch($input_value1) {
            case float: {
                $setOutput_added($activation, $input_value1 + (<float>$input_value2));
            }
            case string: {
                $setOutput_added($activation, $input_value1 + (<string>$input_value2));
            }
        }
    }
    action<Activation, any> $setOutput_added;
    constant string $OUTPUT_TYPE_added := "sameAsAll(value1, value2)";
}
```

Using the constant `sameAsAll` is equivalent to:

```Java
event Add {
    BlockBase $base;
    action $validate() {
        if $base.getInputTypeName("value1") != $base.getInputTypeName("value2") {
            throw L10N.getLocalizedException_basic("block_msg_Add_DifferentTypes");
        }
    }
    action $process(Activation $activation, any $input_value1, any $input_value2) {
        switch($input_value1) {
            case float: {
                $setOutput_added($activation, $input_value1 + (<float>$input_value2));
            }
            case string: {
                $setOutput_added($activation, $input_value1 + (<string>$input_value2));
            }
        }
    }
    action<Activation, any> $setOutput_added;
    action $outputType_added() returns string {
        return $base.getInputTypeName("value1");
    }
}
```


[< Prev: Partition values](070-Partitions.md) | [Contents](000-contents.md) | [Next: The Value type >](090-ValueType.md) 
