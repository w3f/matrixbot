#!/bin/sh

ENVIRONMENT=$1

/scripts/deploy.sh -c ${ENVIRONMENT} -t helm \
                   --set botUser="${MATRIXBOT_USER}" \
                   --set botPassword="${MATRIXBOT_PASSWORD}" \
                   --set roomId="${MATRIXBOT_ROOM_ID}" \
                   --set image.tag="${CIRCLE_TAG}" \
                   matrixbot \
                   w3f/matrixbot
