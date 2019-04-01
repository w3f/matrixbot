#!/bin/bash

source /scripts/common.sh
source /scripts/bootstrap-helm.sh


run_tests() {
    echo Running tests...

    wait_pod_ready matrixbot
}

teardown() {
    helm delete --purge matrixbot
}

main(){
    if [ -z "$KEEP_W3F_MATRIXBOT" ]; then
        trap teardown EXIT
    fi

    /scripts/build-helm.sh \
        --set environment=ci \
        --set botUser="${MATRIXBOT_USER}" \
        --set botPassword="${MATRIXBOT_PASSWORD}" \
        --set roomId="${MATRIXBOT_ROOM_ID}" \
        --set image.tag=${CIRCLE_SHA1} \
        matrixbot \
        ./charts/matrixbot

    run_tests
}

main
