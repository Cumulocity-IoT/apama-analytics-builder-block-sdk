# Using Software AG Designer

While blocks may be written in any text editor, Software AG Designer provides syntax highlighting, completion proposals and error reporting. So that Designer can provide completion proposals, it needs to be configured with the location of the block SDK. You can do this with the `analytics_builder configure designer` command line, which should be run from an **Apama Command Prompt** window.

After the `configure designer` command has run, close Software AG Designer if it is already running and then start it. Create an Apama project within Designer, and add the **Analytics Builder (Support for building blocks)** bundle.

While it is possible to run the correlator from within Software AG Designer, it is recommended to use the included PySys test framework for executing blocks. See [Testing blocks](035-Testing.md).


[< Prev: Introduction](005-Intro.md) | [Contents](000-contents.md) | [Next: Basic blocks >](010-BasicBlocks.md) 
