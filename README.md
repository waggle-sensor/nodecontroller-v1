<!--
waggle_topic=/node_controller/introduction
-->

# Node Stack - Node Controller Repo

This repo contains software and tools specific to the node controller, covering functionality such as:

* Managing data connections. (RabbitMQ Shovels)
* Managing management connections. (Reverse SSH Tunnel)
* Wagman interaction.

## Setup

First, we assume that the [core](https://github.com/waggle-sensor/core) repo has already been set up on a device.

The node controller dependencies and services can then be installed and configured by running:

```sh
git clone https://github.com/waggle-sensor/core /usr/lib/waggle/nodecontroller
cd /usr/lib/waggle/nodecontroller
./configure --system --server-host=$YOUR_BEEHIVE_IP
```

where $YOUR_BEEHIVE_IP is the IP address of your beehive server.
