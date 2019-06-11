#!/bin/sh

if [ "${ENVIRONMENT}" = "w3f" ]; then
    MATRIXBOT_USER="${W3F_MATRIXBOT_USER}"
    MATRIXBOT_PASSWORD="${W3F_MATRIXBOT_PASSWORD}"
    MATRIXBOT_ROOM_ID="${W3F_MATRIXBOT_ROOM_ID}"
    MATRIXBOT_HOMESERVER="https://matrix.web3.foundation"
else
    MATRIXBOT_USER="${COMM_MATRIXBOT_USER}"
    MATRIXBOT_PASSWORD="${COMM_MATRIXBOT_PASSWORD}"
    MATRIXBOT_ROOM_ID="${COMM_MATRIXBOT_ROOM_ID}"
    MATRIXBOT_HOMESERVER="https://matrix.polkadot.builders"
fi

/scripts/deploy.sh -c ${ENVIRONMENT} -t helm -- \
                   --set botUser="${MATRIXBOT_USER}" \
                   --set botPassword="${MATRIXBOT_PASSWORD}" \
                   --set roomId="${MATRIXBOT_ROOM_ID}" \
                   --set homeserver="${MATRIXBOT_HOMESERVER}" \
                   --set image.tag="${CIRCLE_TAG}" \
                   matrixbot \
                   w3f/matrixbot
