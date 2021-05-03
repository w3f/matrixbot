#!/bin/bash

source /scripts/common.sh
source /scripts/bootstrap-helm.sh


run_tests() {
    echo Running tests...

    wait_pod_ready matrixbot
}

teardown() {
    helm delete matrixbot
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
        --set roomEscalationId="${W3F_MATRIXBOT_ESCALATION_ROOM_ID}" \
        --set image.tag=${CIRCLE_SHA1} \
        matrixbot \
        ./charts/matrixbot

    run_tests
}

main
