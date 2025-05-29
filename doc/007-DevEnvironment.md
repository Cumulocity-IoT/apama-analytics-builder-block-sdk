# Developing blocks locally

Blocks may be written in any text editor, but for a more convenient development experience see the [Apama extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ApamaCommunity.apama-extensions). This provides features such as syntax highlighting, completion proposals, and problem markers to quickly identify any errors in your block code. Note that this extension is maintained by the community on a best-effort basis, and is not a supported product. 

The setup steps are:
1. **Install Visual Studio Code**: Download and install `Visual Studio Code <https://code.visualstudio.com/>`_.
2. **Install Apama Extension**: Install the `Apama extension <https://marketplace.visualstudio.com/items?itemName=ApamaCommunity.apama-extensions>`_ from the Visual Studio Code Marketplace.
3. Following the steps listed on the extension page above to setup WSL (if using Windows) and to install a container engine for running Apama inside a container, or else install Apama locally.

The best way to start block development is to create a new repository based on the 
[Streaming Analytics Sample Repository Template](https://github.com/Cumulocity-IoT/streaming-analytics-sample-repo-template). 
Go to that page in GitHub, and click the button to "Use this template" and then "Create a new repository".

To open your new repository in VS Code, open the VS Code command palette (`F1`), run `Dev Containers: Clone Repository in Container Volume` 
and then enter the `https://` link to your GitHub repository. This assumes you have a container engine installed.

Alternatively you can use a web browser to open the repository in [GitHub Codespaces](https://github.com/features/codespaces) without installing anything at all. 
If you prefer to use a local installation of Apama instead of a container, you need to `git clone` your own repository and the [Block SDK](https://github.com/Cumulocity-IoT/apama-analytics-builder-block-sdk) to the correct relative path (as described in the template repository), then you can open your repository folder in VS Code. 

If using the template, your project will have both the main Analytics Builder bundle `../../apama-analytics-builder-block-sdk/bundles/AnalyticsBuilder.bnd` and also the Cumulocity-specific helpers from `../apama-analytics-builder-block-sdk/bundles/CumulocityHelper.bnd`. 

You can now use VS Code to edit the sample block (in the `src/` folder of the template repository) and replace it with your own creation. 

For trying out your blocks and testing that they work correctly, we recommend the PySys test framework (which is included in the Apama containers and installation packages). See [Testing blocks](035-Testing.md).

[< Prev: Introduction](005-Intro.md) | [Contents](000-contents.md) | [Next: Basic blocks >](010-BasicBlocks.md) 
