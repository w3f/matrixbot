#!/bin/sh

/scripts/deploy.sh helm \
                   --set accessToken=${MATRIXBOT_ACCESS_TOKEN} \
                   --set image.tag=${CIRCLE_TAG} \
                   --set alertServiceId=${MATRIXBOT_ALERT_SERVICE_ID} \
                   matrixbot \
                   w3f/matrixbot
