import os, sys
from checkApamaInstallation import confirmFullInstallation

def run(args):
    confirmFullInstallation()
    # Check the command has been executing from Apama command prompt
    apama_home = os.getenv('APAMA_HOME', '')

    filename = "%s/../Designer/extensions/analyticsBuilder.ste" % apama_home
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Creating .ste file under designer extensions folder
    with open(filename, "w") as f:
        f.write('VARIABLE ; ANALYTICS_BUILDER_SDK ; %s ; R \n' % (os.path.abspath(os.path.dirname(sys.argv[0])).replace('\\', '/'),))
        f.write('BUNDLE_CATALOG ; ANALYTICS_BUILDER_SDK/bundles')
    print('Configured designer for Analytics Builder')
