[![CircleCI](https://circleci.com/gh/w3f/matrixbot.svg?style=svg)](https://circleci.com/gh/w3f/matrixbot)

# Helm chart for matrix.org chatbot

This repo includes the manifests for packaging [opsdroid](https://github.com/opsdroid/opsdroid)
as a Helm Chart and extends it with some skills. It also has defined CI
automation for testing and deploying the chart on repo changes.

## Files

These are the main directories in the repo:

* `charts`: contains the matrixbot helm chart, besides the deployment and
service resources it contains manifests for these custom resources:

  * `servicemonitor`: allows to scrape metrics from matrixbot.

  * `certificate`: defines the SSL certificate for `matrixbot.web3.foundation`,
  some of the tasks of the bot require being accessible from outside (eg.
  incoming alert notifications or webhooks).

  * `ingress`: sets how matrixbot service is accessed from outside the cluster.

  * `configmap`: basic configuration of the bot, including the matrix connector
  settings and the skills configuration.

  In order to be able to deploy to production, these environment variables must be
  available:

    * `$ENCRYPTION_KEY`

    * `$MATRIXBOT_ACCESS_TOKEN`

    * `$MATRIXBOT_ALERT_SERVICE_ID`

    * `GITHUB_BOT_TOKEN`

    * `$DOCKER_USER`

    * `$DOCKER_PASSWORD`

  These values are already set on CI, the matrixbot values are available on the
  `Infrastructure` vault on 1Password in an item called `Matrix.org bot`, the
  GitHub bot token in an item called `GitHub bot`, the Docker credentials in an
  item called `Docker Hub Bot`  and the encryption key in the `CI Encryption Key`
  item.

* `.circleci`: defines the CI/CD configuration.

* `scripts`: contains:

  * `integration-tests.sh`: automated checks to verify that the components can
  be properly deployed

  * `deploy.sh`: commands to release the application to the production cluster
  using the published chart.

* `skills`: additional opsdroid functionality, currently the ability to receive
alertmanager notifications on a webhook and show them on a matrix room.

## Workflow

When a PR is proposed to this repo, the integration tests defined by
`scripts/integration-tests.sh` are executed on a Kubernetes cluster created on
CI using the code from the PR, currently they just check that the component can
be deployed and deleted without errors.

After the PR is merged into master, when a semantic version tag (`vX.Y.Z`) is
pushed the tests are run again and, if all is ok, the chart is published and the
bot is deployed to production. Note that the tag version pushed must match the
version in [./charts/matrixbot/Chart.yaml]()

## Running tests

Tests can be run and debugged locally, you need to have [docker](https://docs.docker.com/install/)
and [CircleCI CLI](https://circleci.com/docs/2.0/local-cli/) installed, then run:
```
$ circleci local execute --job integrationTests
```
