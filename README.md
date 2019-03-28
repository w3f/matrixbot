[![CircleCI](https://circleci.com/gh/w3f/matrixbot.svg?style=svg)](https://circleci.com/gh/w3f/matrixbot)

# Helm chart for matrix.org chatbot

This repo includes the manifests for packaging [go-neb](https://github.com/matrix-org/go-neb)
as a Helm Chart. It also has defined CI automation for testing and deploying the
chart on repo changes. The bot itself is configured to just respond to `echo`
commands, the main usage currently is showing alertmanager notifications.

## Files

These are the main directories in the repo:

* `charts`: contains the matrixbot helm chart, besides the deployment and
service resources it contains manifests for these custom resources:

  * `servicemonitor`: allows to scrape metrics from matrixbot.

  * `certificate`: defines the SSL certificate for `matrixbot.web3.foundation`,
  some of the tasks of the bot require being accessible from outside (eg.
  incoming alert notifications or webhooks).

  * `ingress`: sets how matrixbot service is accessed from outside the cluster.

  * `persistentvolumeclaim`: declares a persistent storage for the bot database,
  so that if the bot container is restarted the state can be recovered.

  * `configmap`: basic configuration of the bot, sets the access token and only
  enables the `echo` service.

  In order to be able to deploy to production, these environment variables must be
  available:

    * `$ENCRYPTION_KEY`

    * `$MATRIXBOT_ACCESS_TOKEN`

    * `GITHUB_BOT_TOKEN`

  These values are already set on CI, the matrixbot access token is available on
  the `Infrastructure` vault on 1Password in an item called `Matrix.org bot`,
  the GitHub bot token in a item called `GitHub bot` and the encryption key in
  the `CI Encryption Key` item.

* `.circleci`: defines the CI/CD configuration.

* `scripts`: contains:

  * `integration-tests.sh`: automated checks to verify that the components can
  be properly deployed

  * `deploy.sh`: commands to release the application to the production cluster
  using the published chart.

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
