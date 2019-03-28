#!/bin/sh

/scripts/deploy.sh helm \
                   --set accessToken=$MATRIXBOT_ACCESS_TOKEN \
                   matrixbot \
                   w3f/matrixbot
