# Developing blocks locally

Blocks may be written in any text editor, but for a more convenient development experience you may wish to try the [Apama extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ApamaCommunity.apama-extensions). This provides features such as syntax highlighting and problem markers to quickly identify any errors in your block code. Note that this extension is maintained by the community on a best-effort basis, and is not a supported product. 

See the extension's documentation for details of how to get it installed (including the steps for running Visual Studio Code on Windows using the Apama installation packages for Linux). 

To use the extension for block development you need to create an Apama project for your blocks, and add the bundle which makes available the same EPL APIs that will be used when your blocks are deployed to Cumulocity. To do this:
1. Install the latest version of the Apama `dev` package. If you have Docker available, you might instead run the following commands from within a `builder` container image, or use the dev container at https://github.com/Cumulocity-IoT/cumulocity-analytics-vsc-devcontainer/
2. Download (or `git clone`) this SDK. We recommend ensuring the directory is named `apama-analytics-builder-block-sdk` (i.e. the same as the repository, without any extra version number). 
3. Create an Apama project for your blocks, next to the block SDK directory: `apama_project create my-block-project`
4. Change into your project directory and add the Analytics Builder block support bundle using a relative path:
   ```
   cd my-block-project
   apama_project add bundle ../apama-analytics-builder-block-sdk/bundles/AnalyticsBuilder.bnd
   ``` 
5. Optionally: if you will be using the Cumulocity-specific helpers in your blocks, also add `../apama-analytics-builder-block-sdk/bundles/CumulocityHelper.bnd`
6. You can now open Visual Studio Code, install the [Apama extension](https://marketplace.visualstudio.com/items?itemName=ApamaCommunity.apama-extensions) and create your first block. 

For trying out your blocks and testing that they work correctly, we recommend the PySys test framework (which is included in the Apama installation). See [Testing blocks](035-Testing.md).

[< Prev: Introduction](005-Intro.md) | [Contents](000-contents.md) | [Next: Basic blocks >](010-BasicBlocks.md) 
