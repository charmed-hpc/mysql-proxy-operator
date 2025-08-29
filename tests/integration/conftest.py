#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configure MySQL database proxy integration tests."""

import logging
import os
from collections.abc import Iterator
from pathlib import Path

import jubilant
import pytest

logger = logging.getLogger(__name__)
LOCAL_MYSQL_PROXY = Path(mysql_proxy) if (mysql_proxy := os.getenv("LOCAL_MYSQL_PROXY")) else None


@pytest.fixture(scope="session")
def juju(request: pytest.FixtureRequest) -> Iterator[jubilant.Juju]:
    """Yield wrapper for interfacing with the `juju` CLI command."""
    keep_models = bool(request.config.getoption("--keep-models"))

    with jubilant.temp_model(keep=keep_models) as juju:
        juju.wait_timeout = 10 * 60  # Timeout after 10 minutes.

        yield juju

        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")


@pytest.fixture(scope="function")
def fast_forward(juju: jubilant.Juju) -> Iterator[None]:
    """Temporarily increase the rate of `update-status` event fires to 10s."""
    old_interval = juju.model_config()["update-status-hook-interval"]
    juju.model_config({"update-status-hook-interval": "10s"})

    yield

    juju.model_config({"update-status-hook-interval": old_interval})


@pytest.fixture(scope="module")
def base(request: pytest.FixtureRequest) -> str:
    """Get the base to deploy the Slurm charms on."""
    return request.config.getoption("--charm-base")


@pytest.fixture(scope="module")
def mysql_proxy(request: pytest.FixtureRequest) -> Path | str:
    """Get the `mysql-proxy` charm to use for the integration tests.

    If the `LOCAL_MYSQL_PROXY` environment variable is not set,
    the `mysql-proxy` charm will be pulled from the `latest/edge` channel
    on Charmhub instead.

    Returns:
        `Path` object if using a local `mysql-proxy` charm. `str` if pulling from Charmhub.
    """
    if not LOCAL_MYSQL_PROXY:
        logger.info("pulling `mysql-proxy` charm from the `latest/edge` channel on charmhub")
        return "slurmd"

    logger.info("using local `mysql-proxy` charm located at %s", LOCAL_MYSQL_PROXY)
    return LOCAL_MYSQL_PROXY
