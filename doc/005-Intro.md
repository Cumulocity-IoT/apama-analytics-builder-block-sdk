# Introduction

This Software Development Kit (SDK) describes how to write blocks for Apama Analytics Builder. Analytics Builder allows users to create "models" by combining a number of blocks, providing parameter values for the blocks, and wiring the blocks together. Models use blocks to implement streaming analytics, for example, to detect anomalous conditions or to generate derived measurements for further analysis. Blocks can implement connectivity to receive data from outside the model, send data outside the model, or to perform processing based on values flowing through the model.

Analytic models run in the Apama correlator, and are managed by the Analytics Builder framework. The framework is responsible for checking that the model wiring is valid, the lifetime of the model, and invoking blocks when values flow through a model.

Blocks can be tested using the PySys test framework that is included in an Apama installation. In order to develop, test and package blocks, you will need a full installation of Apama.

Blocks are implemented in Apama's Event Processing Language (EPL). This guide assumes a working knowledge of EPL. Refer to the [Apama documentation on developing EPL applications](http://www.apamacommunity.com/documents/10.7.2.0/apama_10.7.2.0_webhelp/apama-webhelp/#page/apama-webhelp%2Fco-DevApaAppInEpl_how_this_book_is_organized.html) and the [API Reference for EPL (ApamaDoc)](http://www.apamacommunity.com/documents/10.7.2.0/apama_10.7.2.0_webhelp/ApamaDoc/index.html). This guide also assumes a working knowledge of the Analytics Builder data model. Refer to the [Apama Analytics Builder documentation](https://documentation.softwareag.com/onlinehelp/Rohan/Analytics_Builder/pab10-9-0/apama-pab-webhelp/index.html#page/apamaanalyticsbuilder-webhelp%2Fto-AnaBui_getting_started_with_apama_analytics_builder.html). 

The Analytics Builder block SDK has branches in a GitHub repository. You need to download the appropriate release of the block SDK based on the version of the Cumulocity IoT tenant you are using. Refer to the [Releases](https://github.com/SoftwareAG/apama-analytics-builder-block-sdk/releases) page of the block SDK. The version of the block SDK should be compatible with the version of the Cumulocity IoT tenant. 

Blocks can range from very simple stateless functions to more complex logic. Blocks can make use of:

* **Parameters** - these are values provided when a model is activated. Blocks can validate that the parameters are legal. Parameters can be optional, of numeric, boolean, string, enumeration or list types.
* **State** - the framework holds the state and provides it to the block when needed. The framework can provide different states for different partitions of a model. (For example, within Cumulocity IoT, a model can apply to a device group, and the model will have a separate state for each device within the group).
* **Inputs and outputs** - these allow the block to connect with wires to other blocks within the model.
* **Sending and receiving events** - this allows the block to interact with external data sources or sinks, or to other models or even EPL applications.
* **Documentation** - a block can include in-line ApamaDoc documenting the behavior of the block, parameters, inputs and outputs. This is visible in the documentation pane of the model editor part of Analytics Builder.

[< Prev: Contents](000-contents.md) | [Contents](000-contents.md) | [Next: Using Software AG Designer >](007-UsingDesigner.md) 
