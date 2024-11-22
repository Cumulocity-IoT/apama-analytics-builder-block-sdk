# Testing blocks

Blocks can be tested using the PySys testing framework. This is included in the Apama installation, along with extensions for using Apama with PySys. Built on top of the Apama extensions is a framework to test blocks. Refer to the [Apama Python API documentation](https://documentation.softwareag.com/pam/10.15.5/en/webhelp/pydoc/index.html).

The samples include tests. The `pysystestproject.xml` configuration relies on the environment variable `ANALYTICS_BUILDER_SDK` being set to the location of the block SDK using an absolute path. PySys tests should contain a `run.py` with a class that extends `apama.analyticsbuilder.basetest:AnalyticsBuilderBaseTest`. In the `execute` method of the test, start a correlator with the `self.startAnalyticsBuilderCorrelator()` method. This starts a correlator, injects the Analytics Builder framework into it, and returns a `CorrelatorHelper` object. Provide a `blockSourceDir` parameter with the path to the source of the blocks, typically within the project tree (use `self.project.SOURCE` from the supplied `pysysproject.xml` file). Then, create a model to test the block with the `self.createTestModel('<blockUnderTest>')`  This results in a model being activated in the correlator with an input and output connected to every input and output of the block, and an identifier of the model is returned. The block can be exercised by sending events created by the `self.inputEvent` method, for a given block input identifier.


Both `createTestModel` and `inputEvent` take an optional argument: `id` - an identifier of the model. If an identifier is not specified, `createModel` will use the identifiers `model_0` and upwards, and `inputEvent` will use `model_0` (that is, the first created model).

`createTestModel` takes these arguments:

* `blockUnderTest` (required) - string of a single block's fully qualified identifier, or a list of blocks (in which case a wiring list is required, and keys of the parameters argument must be prefixed with the blockIndex).
* `parameters` (optional) - dictionary of block parameter identifier to value. If there are multiple blocks, each block is prefixed with the block index.
* `id` (optional) - identifier of the model
* `corr` (optional) - correlator to use; defaults to using the last correlator started by `startAnalyticsBuilderCorrelator`.
* `inputs` (optional) - a dictionary that maps the input names to their types.  For example `{ "input1" : "string", "input2" : "integer" }`. If an input identifier is not specified, the input defaults to the `float` type. If the value for the identifier is set to `None` or an empty string, that input is not connected.
* `wiring` (optional unless testing multiple blocks) - list of strings containing source block index, output port identifier, target block index, input port identifier separated by colons - e.g. `['0:timeWindow:1:window']`


The following methods can be used to check the output of the block is as expected:

* `assertBlockOutput` checks that the series of outputs generated from a given outputId are as supplied in a list of values.  (optional parameters for partitionId and modelId)
* `outputFromBlock` returns a list of the values sent to the named outputId (optional parameter for partitionId and modelId)
* `allOutputFromBlock` returns a list of all of the outputs from a block, a list of dictionaries where each dictionary has `outputId`, `partitionId`, `time`, `properties` and `value` entries.


Note that the correlator started by `startAnalyticsBuilderCorrelator` is externally clocked, meaning that the correlator's time increments only when a timestamp event is received. Consequently, events arriving between timestamp events are assigned the same time, that is, the time of the last timestamp.

After a timestamp is received, subsequent events are held until the next timestamp event that has a time at least 0.1s greater. All of the events are then processed together. If a value for a particular input is received while an event for that input is already waiting, only one of the events will be retained and then sent to the model. The other value will be discarded. (Whether this is the new value or the existing, waiting value is undefined.)

The `timestamp` method can be used to generate a time pseudo-event when testing. If events modifying multiple inputs are sent to the model between timestamps (and those timestamps are at least 0.1 seconds apart), the new values will be received by the model simultaneously and evaluated once. For an example of this, see the **GroupStatistics_Bounded** test sample in the in the **samples/tests** directory.

For example, a simple test is:

```python
from pysys.constants import *
from apamax.analyticsbuilder.basetest import AnalyticsBuilderBaseTest

class PySysTest(AnalyticsBuilderBaseTest):
    def execute(self):
        correlator = self.startAnalyticsBuilderCorrelator(
            blockSourceDir=f'{self.project.SOURCE}/blocks/')
        modelId = self.createTestModel('apamax.analyticsbuilder.samples.Offset')
        self.sendEventStrings(correlator,
                              self.timestamp(1),
                              self.inputEvent('value', 100.75, id=modelId),
                              self.timestamp(2),
                              self.inputEvent('value', 10.50, id=modelId),
                              self.timestamp(2.1),
                              )

    def validate(self):
        self.assertBlockOutput('output', [200.75, 110.50])

```

And will generate outputs at times 1 and 2, but the `self.timestamp(2.1)` is required to trigger the events at time 2.

Points to be aware of:

* If using `sendEvents` (that is, from a file), include a `&FLUSHING(5)` line at the start of the file. This ensures events are processed completely to avoid race conditions. `self.sendEventStrings` will do this automatically.
* If using `assertGrep` on floating point numbers, beware of rounding errors (for example, a result of `4.6` may be rendered as `4.599999999997` in an event file due to rounding errors).

For examples, see the tests in the **samples/tests** directory.

[< Prev: Building a block into an extension](030-BuildingExtensions.md) | [Contents](000-contents.md) | [Next: Parameters, block startup and error handling >](040-Parameters.md) 
