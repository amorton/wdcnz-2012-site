#!/bin/bash

DOWNLOAD_CACHE=${PIP_DOWNLOAD_CACHE:-"/tmp/downloads/pip"}
mkdir -p $DOWNLOAD_CACHE
sudo chmod 777 $DOWNLOAD_CACHE

# When installing on a prod server the virtualenv exe will be in the 
# non default python install. Check the env var so we can reference it 
# directly.
VIRTUALENV_PATH=${VIRTUALENV_PATH:-"virtualenv"}
$VIRTUALENV_PATH --no-site-packages --distribute .dev-env

# important that we use easy_install to install readline
# otherwise ipython will not pick it up inside the env. 
.dev-env/bin/easy_install readline
 
.dev-env/bin/pip install --download-cache=$DOWNLOAD_CACHE -r requirements.txt
