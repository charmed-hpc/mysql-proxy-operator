# MySQL proxy operator

![GitHub License](https://img.shields.io/github/license/charmed-hpc/mysql-proxy-operator)
[![Matrix](https://img.shields.io/matrix/ubuntu-hpc%3Amatrix.org?logo=matrix&label=ubuntu-hpc)](https://matrix.to/#/#hpc:ubuntu.com)

A [Juju](https://juju.is) charm for proxying uncharmed MySQL servers to charmed applications.

## ✨ Getting Started

To use an external, uncharmed MySQL database in place of deploying a Juju-managed MySQL
instance with, create the `mysql-proxy-db-uri` secret and set the appropriate
proxy charm configuration. See the instructions below for an example on how to set up
an external MySQL database running in Docker with the MySQL proxy operator.

### Step 1: Set up external MySQL database with Docker

```shell
docker run --name mysql-slurmdbd \
    -e MYSQL_USER=testuser \
    -e MYSQL_PASSWORD=testpassword \
    -e MYSQL_DATABASE=slurm_acct_db \
    -e MYSQL_ALLOW_EMPTY_PASSWORD=true \
    -p 3306:3306 \
    -d mysql:8.4
```

### Step 2: Configure Juju infrastructure

```shell
juju add-model external-mysql

ip=$(hostname -i)
secret_id=$(juju add-secret mysql-proxy-db-uri db-uri="mysql://testuser:testpassword@$ip:3306")

juju deploy mysql-proxy --config db-uri=$secret_id
juju deploy slurmdbd --channel latest/edge
juju deploy slurmctld --channel latest/edge
juju deploy slurmd --channel latest/edge
juju grant-secret mysql-proxy-db-uri mysql-proxy

juju integrate mysql-proxy slurmdbd
juju integrate slurmctld slurmdbd
juju integrate slurmctld slurmd
```

## 🤔 What's next?

If you want to learn more about all the things you can do with the MySQL proxy operator,
or have any further questions on what you can do with the operator, here are some
further resources for you to explore:

* [Charmed HPC documentation](https://canonical-charmed-hpc.readthedocs-hosted.com/latest/)
* [Open an issue](https://github.com/charmed-hpc/mysql-proxy-operator/issues/new?title=ISSUE+TITLE&body=*Please+describe+your+issue*)
* [Ask a question on GitHub](https://github.com/orgs/charmed-hpc/discussions/categories/q-a)

## 🛠️ Development

The project uses [just](https://github.com/casey/just) and [uv](https://github.com/astral-sh/uv) for
development, which provides some useful commands that will help you while hacking on the MySQL proxy operator:

```shell
just fmt            # Apply formatting standards to code.
just lint           # Check code against coding style standards.
just woke           # Run inclusive naming checks.
just typecheck      # Run static type checks.
just unit           # Run unit tests.
```

If you're interested in contributing, take a look at our [contributing guidelines](./CONTRIBUTING.md).

## 🤝 Project and community

The MySQL proxy operator is a project of the [Ubuntu High-Performance Computing community](https://ubuntu.com/community/governance/teams/hpc).
Interested in contributing bug fixes, patches, documentation, or feedback? Want to join the
Ubuntu HPC community? You’ve come to the right place 🤩

Here’s some links to help you get started with joining the community:

* [Ubuntu Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct)
* [Contributing guidelines](./CONTRIBUTING.md)
* [Join the conversation on Matrix](https://matrix.to/#/#hpc:ubuntu.com)
* [Get the latest news on Discourse](https://discourse.ubuntu.com/c/hpc/151)
* [Ask and answer questions on GitHub](https://github.com/orgs/charmed-hpc/discussions/categories/q-a)

## 📋 License

The MySQL proxy operator is free software, distributed under the Apache Software License,
version 2.0. See the [Apache-2.0 LICENSE](./LICENSE) file for further details.
