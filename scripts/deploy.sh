#!/bin/sh

RELEASE_NAME="matrixbot"
if [ "${ENVIRONMENT}" = "w3f" ]; then
    MATRIXBOT_USER="${W3F_MATRIXBOT_USER}"
    MATRIXBOT_PASSWORD="${W3F_MATRIXBOT_PASSWORD}"
    MATRIXBOT_ROOM_ID="${W3F_MATRIXBOT_ROOM_ID}"
else
    MATRIXBOT_USER="${COMM_MATRIXBOT_USER}"
    MATRIXBOT_PASSWORD="${COMM_MATRIXBOT_PASSWORD}"
    if [ "${APP}" = "eth" ]; then
        MATRIXBOT_ROOM_ID="${ETH_MATRIXBOT_ROOM_ID}"
        RELEASE_NAME="matrixbot-ethereum-tracker"
    else
        MATRIXBOT_ROOM_ID="${COMM_MATRIXBOT_ROOM_ID}"
    fi
fi

/scripts/deploy.sh -c ${ENVIRONMENT} -t helm -- \
                   --set botUser="${MATRIXBOT_USER}" \
                   --set botPassword="${MATRIXBOT_PASSWORD}" \
                   --set roomId="${MATRIXBOT_ROOM_ID}" \
                   --set image.tag="${CIRCLE_TAG}" \
                   "${RELEASE_NAME}" \
                   w3f/matrixbot
