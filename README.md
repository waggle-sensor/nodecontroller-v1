<!--
waggle_topic=/node_controller/introduction
-->

# _This repo is archived. See https://github.com/waggle-sensor/nodecontroller_

# Node Stack - Node Controller Repo

This repo contains software and tools specific to the node controller, covering functionality such as:

* Managing data connections. (RabbitMQ Shovels)
* Managing management connections. (Reverse SSH Tunnel)
* Wagman interaction.

Note that this software was originally targetting the ODROID C1+, so some components may require
significant tweaks before running them on other devices.

## Setup

First, we assume that the [core](https://github.com/waggle-sensor/core) repo has already been set up on a device.

The node controller dependencies and services can then be installed and configured by running:

```sh
git clone https://github.com/waggle-sensor/nodecontroller /usr/lib/waggle/nodecontroller
cd /usr/lib/waggle/nodecontroller
./configure --system --server-host=$YOUR_BEEHIVE_IP
```

Leaving out the `--system` and `--server-host` flags will only install dependencies and services, but will not
setup data or management connectivity.
