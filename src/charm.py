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

"""Charmed operator for proxying uncharmed MySQL databases to charmed applications."""

import logging

import ops
from charms.data_platform_libs.v0.data_interfaces import DatabaseProvides, DatabaseRequestedEvent
from hpc_libs.interfaces import block_unless
from hpc_libs.utils import StopCharm, leader, refresh

import proxy
from constants import DATABASE_INTEGRATION_NAME, DB_URI_SECRET_LABEL
from state import check_mysql_proxy, db_uri_secret_exists

logger = logging.getLogger(__name__)
refresh = refresh(hook=check_mysql_proxy)
refresh.__doc__ = """Refresh status of the mysql proxy unit after an event handler completes."""


class MySQLProxyCharm(ops.CharmBase):
    """Charmed operator for proxying uncharmed MySQL databases to charmed applications."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(self.on.secret_changed, self._on_secret_changed)

        self.mysql = DatabaseProvides(self, DATABASE_INTEGRATION_NAME)
        framework.observe(self.mysql.on.database_requested, self._on_database_requested)

    @refresh
    def _on_install(self, _: ops.InstallEvent):
        if not self.unit.is_leader():
            raise StopCharm(
                ops.BlockedStatus(
                    "MySQL proxy high-availability is not supported. Scale down application"
                )
            )

    @leader
    @refresh
    @block_unless(db_uri_secret_exists)
    def _on_config_changed(self, _: ops.ConfigChangedEvent):
        """Handle when the proxy's configuration is changed."""
        try:
            data = proxy.load_database_data(self)
        except ValueError as e:
            logger.error(e)
            raise StopCharm(
                ops.BlockedStatus("Failed to load database URI. See `juju debug-log` for details")
            )

        proxy.set_database_data(self, data)

    @leader
    @refresh
    @block_unless(db_uri_secret_exists)
    def _on_secret_changed(self, event: ops.SecretChangedEvent) -> None:
        """Handle when the database URI secret is changed."""
        if event.secret.label != DB_URI_SECRET_LABEL:
            return

        try:
            data = proxy.load_database_data(self)
        except ValueError as e:
            logger.error(e)
            raise StopCharm(
                ops.BlockedStatus("Failed to load database URI. See `juju debug-log` for details")
            )

        proxy.set_database_data(self, data)

    @leader
    @refresh
    @block_unless(db_uri_secret_exists)
    def _on_database_requested(self, event: DatabaseRequestedEvent) -> None:
        """Handle when a client requests a database."""
        try:
            data = proxy.load_database_data(self)
        except ValueError as e:
            logger.error(e)
            raise StopCharm(
                ops.BlockedStatus("Failed to load database URI. See `juju debug-log` for details")
            )

        proxy.set_database_data(self, data, integration_id=event.relation.id)


if __name__ == "__main__":  # pragma: nocover
    ops.main(MySQLProxyCharm)
