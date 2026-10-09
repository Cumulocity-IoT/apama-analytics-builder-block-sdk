# Logging from blocks

Log messages from blocks are shown on the **Logs** page of the Streaming Analytics application and in the logs pane of the model editor. See [Viewing logs in the Streaming Analytics application](https://cumulocity.com/docs/streaming-analytics/troubleshooting/#logs-view) and [Viewing the logs of a model](https://cumulocity.com/docs/streaming-analytics/analytics-builder/#viewing-the-logs-of-a-model) in the Cumulocity documentation.

A log message from a custom block is only shown there if the block follows the conventions described below. The framework does not add a prefix to, or check, the messages that custom blocks log themselves. Custom blocks are expected to follow these conventions, but nothing forces them to.

## Using the log prefix

The simplest way to follow the conventions is to start each log message with the prefix returned by the `getLogPrefix()` action of the block's `$base` member:

```java
action $process(Activation $activation, float $input_value) {
    log $base.getLogPrefix() + "Received value " + $input_value.toString() at INFO;
}
```

The prefix identifies the tenant and the model (or template model instance) that the block belongs to. A message must meet the following requirements to be shown:

* It is written with an EPL `log` statement. Output written with `print` is not shown.
* It starts with the prefix. Nothing can come before it, not even a space.
* It is a single line. Do not include line breaks in the message. If a message contains line breaks, only its first line is shown, because the following lines do not start with the prefix.

## Building the prefix yourself

If you cannot use `getLogPrefix()`, build the prefix yourself. It has the following structure, followed by a single space and then the message text:

```text
[<tenantId>|model=<modelId>]
```

where:

* `<tenantId>` is the ID of the tenant that the model runs in, for example, `t12345`.
* `<modelId>` is the ID of the model. For a template model instance, it is the ID of the instance.
* A backslash (`\`), closing square bracket (`]`), or vertical bar (`|`) in the model ID is escaped with a preceding backslash.

For example, `[t12345|model=87104] Received value 42` is shown in the logs of model `87104` of tenant `t12345`. A message with only the tenant ID, such as `[t12345] Connection restored`, is shown on the **Logs** page when no model is selected, but not in the logs of any model.

Messages that do not start with a valid prefix are not shown on the **Logs** page or in the model editor. They are still written to the log file of the Apama-ctrl microservice. See [Log files of the Apama-ctrl microservice](https://cumulocity.com/docs/streaming-analytics/troubleshooting/#logfiles) in the Cumulocity documentation.

**Important:** The framework does not check the prefix of messages written by custom blocks. A custom block that writes an incorrect prefix causes its messages to be shown for a different model, or not at all. Do not add other fields to the prefix. A prefix with other fields is not valid.

[< Prev: Parameters, block startup and error handling](040-Parameters.md) | [Contents](000-contents.md) | [Next: Blocks with state >](050-State.md) 
