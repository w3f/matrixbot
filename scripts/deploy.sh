#!/bin/sh

/scripts/deploy.sh helm \
                   --set botUser="${MATRIXBOT_USER}" \
                   --set botPassword="${MATRIXBOT_PASSWORD}" \
                   --set roomId="${MATRIXBOT_ROOM_ID}" \
                   --set image.tag="${CIRCLE_TAG}" \
                   matrixbot \
                   w3f/matrixbot
