#!/bin/bash

source /scripts/common.sh
source /scripts/bootstrap-helm.sh


run_tests() {
    echo Running tests...
}

teardown() {
    helmfile delete --purge
}

main(){
    if [ -z "$KEEP_W3F_BASE_SERVICES" ]; then
        trap teardown EXIT
    fi

    source ./scripts/preflight.sh
    source /scripts/build-helmfile.sh

    run_tests
}

main
