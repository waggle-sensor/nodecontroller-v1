<!--
waggle_topic=/node_controller/introduction
-->

# Node Stack - Node Controller Repo

This repo contains software and tools specific to the node controller, covering functionality such as:

* Managing data connections. (AMQPS / RabbitMQ Shovels)
* Managing management connections. (Reverse SSH Tunnel)
* Wagman interaction.

## Setup

First, we assume that the [core](https://github.com/waggle-sensor/core) repo has already been set up on a device.

The node controller dependencies and services can then be installed and configured by running:

```sh
./configure --system --server-host=BEEHIVE_IP
```
