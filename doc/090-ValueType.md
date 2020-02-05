# The Value type

Most blocks deal with simple values of types `float`, `string`, `boolean` or `pulse`. However, it is also possible to provide extra properties alongside these values. For example, the Cumulocity blocks provide both a float (from a `Measurement`) or pulse (for an `Event`) and any extra properties provided in the `Measurement` or `Event` object. For this, use the `Value` type.

The `Value` type has a `value` field of type `any`. This should be of one of the core types `string`, `float` or `boolean`, and the block should declare which of these types (or `pulse`) it will send in `Value` objects. When an output providing `Value` objects is connected to a block with a simple input, the framework unpacks the simple value from the `Value` object. Thus, while the Cumulocity `Measurement` generates `Value` objects with extra properties, these can still be connected to blocks expecting a simple numeric input of type `float`.

If a block uses the `Value` type as an input, it may also specify a `string constant $INPUT_TYPE_<inputId>` if it wants to specify a more exact type.

The **Extract Property** block provided with Analytics Builder is able to extract different properties from a `Value` input, provided the value is one of the core types `string`, `float` or `boolean`.

The entries in the `properties` field of the `Value` can be of any serializable type. Refer to the **Windowing.mon** sample for an example of providing a more complex type.

[< Prev: Dynamic types](080-DynamicTypes.md) | [Contents](000-contents.md) | [Next: Input and output blocks >](100-InputAndOutput.md) 
