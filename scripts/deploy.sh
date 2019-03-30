#!/bin/sh

/scripts/deploy.sh helm \
                   --set accessToken=${MATRIXBOT_ACCESS_TOKEN} \
                   --set image.tag=${CIRCLE_TAG} \
                   matrixbot \
                   w3f/matrixbot
