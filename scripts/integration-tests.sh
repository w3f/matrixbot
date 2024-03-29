#!/bin/bash

source /scripts/common.sh
source /scripts/bootstrap-helm.sh


run_tests() {
    echo Running tests...

    wait_pod_ready matrixbot
    wait_pod_ready ack
}

teardown() {
    helm delete matrixbot
    helm delete ack
}

main(){
    if [ -z "$KEEP_W3F_MATRIXBOT" ]; then
        trap teardown EXIT
    fi

    /scripts/build-helm.sh \
        --set environment=ci \
        --set botUser="${W3F_MATRIXBOT_USER}" \
        --set botPassword="${W3F_MATRIXBOT_PASSWORD}" \
        --set roomId="${W3F_MATRIXBOT_ROOM_ID}" \
        --set image.tag=${CIRCLE_SHA1} \
        matrixbot \
        ./charts/matrixbot

    /scripts/build-helm.sh \
        --set environment=ci \
        --set botUser="${W3F_MATRIXBOT_USER}" \
        --set botPassword="${W3F_MATRIXBOT_PASSWORD}" \
        --set roomId="${W3F_MATRIXBOT_ROOM_ID}" \
        --set image.tag=${CIRCLE_SHA1} \
        --set encryption.enabled=true \
        --set sqliteDB.enabled=true \
        --set escalation.enabled=true \
        --set escalation.roomId1="${W3F_MATRIXBOT_ROOM_ID}" \
        ack \
        ./charts/matrixbot    

    run_tests
}

main
