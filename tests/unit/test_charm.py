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

"""Unit tests for the `mysql-proxy` charmed operator."""

import ops
import pytest
from ops import testing

from constants import DATABASE_INTEGRATION_NAME, DB_URI_SECRET_LABEL

EXAMPLE_DB_URI = "mysql://testuser:testpassword@127.0.0.1:3306"


@pytest.mark.parametrize(
    "leader",
    (
        pytest.param(True, id="leader"),
        pytest.param(False, id="not leader"),
    ),
)
class TestMySQLProxyCharm:
    """Unit tests for the `mysql-proxy` charmed operator."""

    def test_on_install(self, mock_charm, leader) -> None:
        """Test the `_on_install` event handler."""
        state = mock_charm.run(mock_charm.on.install(), testing.State(leader=leader))

        if leader:
            assert state.unit_status == ops.BlockedStatus(
                "Waiting for `mysql-proxy-db-uri` secret to be configured"
            )
        else:
            assert state.unit_status == ops.BlockedStatus(
                "MySQL proxy high-availability is not supported. Scale down application"
            )

    @pytest.mark.parametrize(
        "good_uri",
        (
            pytest.param(True, id="good uri"),
            pytest.param(False, id="bad uri"),
        ),
    )
    @pytest.mark.parametrize(
        "joined",
        (
            pytest.param(True, id="joined"),
            pytest.param(False, id="not joined"),
        ),
    )
    @pytest.mark.parametrize(
        "ready",
        (
            pytest.param(True, id="ready"),
            pytest.param(False, id="not ready"),
        ),
    )
    def test_on_config_changed(self, mock_charm, good_uri, joined, ready, leader) -> None:
        """Test the `_on_config_changed` event handler."""
        db_uri_secret = testing.Secret(
            tracked_content={"db-uri": EXAMPLE_DB_URI if good_uri else "postgres://bigfoot"},
            label=DB_URI_SECRET_LABEL,
        )

        integration_id = 1
        integration = testing.Relation(
            endpoint=DATABASE_INTEGRATION_NAME,
            interface="mysql_client",
            id=integration_id,
            remote_app_name="slurmdbd",
        )

        state = mock_charm.run(
            mock_charm.on.config_changed(),
            testing.State(
                leader=leader,
                relations={integration} if joined else set(),
                secrets={db_uri_secret} if ready else set(),
                config={"db-uri": db_uri_secret.id},
            ),
        )

        if leader and ready:
            assert (
                state.unit_status == ops.ActiveStatus()
                if good_uri
                else ops.BlockedStatus(
                    "Failed to load database URI. See `juju debug-log` for details"
                )
            )
        elif leader and not ready:
            assert state.unit_status == ops.BlockedStatus(
                "Waiting for `mysql-proxy-db-uri` secret to be configured"
            )
        else:
            assert mock_charm.unit_status_history == []

    @pytest.mark.parametrize(
        "good_uri",
        (
            pytest.param(True, id="good uri"),
            pytest.param(False, id="bad uri"),
        ),
    )
    @pytest.mark.parametrize(
        "db_secret",
        (
            pytest.param(True, id="`mysql-proxy-db-uri` secret"),
            pytest.param(False, id="not `mysql-proxy-db-uri` secret"),
        ),
    )
    def test_on_secret_changed(self, mock_charm, db_secret, good_uri, leader) -> None:
        """Test the `_on_secret_changed` event handler."""
        db_uri_secret = testing.Secret(
            tracked_content={"db-uri": EXAMPLE_DB_URI if good_uri else "postgres://bigfoot"},
            label=DB_URI_SECRET_LABEL,
        )
        other_secret = testing.Secret(tracked_content={"another-one": "xyz123"})

        integration_id = 1
        integration = testing.Relation(
            endpoint=DATABASE_INTEGRATION_NAME,
            interface="mysql_client",
            id=integration_id,
            remote_app_name="slurmdbd",
        )

        state = mock_charm.run(
            mock_charm.on.secret_changed(db_uri_secret if db_secret else other_secret),
            testing.State(
                leader=leader,
                relations={integration},
                secrets={db_uri_secret, other_secret},
                config={"db-uri": db_uri_secret.id},
            ),
        )

        if leader:
            assert (
                state.unit_status == ops.ActiveStatus()
                if good_uri
                else ops.BlockedStatus(
                    "Failed to load database URI. See `juju debug-log` for details"
                )
            )
        else:
            assert mock_charm.unit_status_history == []

    @pytest.mark.parametrize(
        "good_uri",
        (
            pytest.param(True, id="good uri"),
            pytest.param(False, id="bad uri"),
        ),
    )
    @pytest.mark.parametrize(
        "ready",
        (
            pytest.param(True, id="ready"),
            pytest.param(False, id="not ready"),
        ),
    )
    def test_on_database_requested(self, mock_charm, good_uri, ready, leader) -> None:
        """Test the `_on_database_requested` event handler."""
        db_uri_secret = testing.Secret(
            tracked_content={"db-uri": EXAMPLE_DB_URI if good_uri else "postgres://bigfoot"},
            label=DB_URI_SECRET_LABEL,
        )

        integration_id = 1
        integration = testing.Relation(
            endpoint=DATABASE_INTEGRATION_NAME,
            interface="mysql_client",
            id=integration_id,
            remote_app_name="slurmdbd",
            remote_app_data={"database": "slurm_acct_db"},
        )

        state = mock_charm.run(
            mock_charm.on.relation_changed(integration),
            testing.State(
                leader=leader,
                relations={integration},
                secrets={db_uri_secret} if ready else set(),
                config={"db-uri": db_uri_secret.id},
            ),
        )

        if leader and ready:
            assert (
                state.unit_status == ops.ActiveStatus()
                if good_uri
                else ops.BlockedStatus(
                    "Failed to load database URI. See `juju debug-log` for details"
                )
            )

            integration = state.get_relation(integration_id)
            assert (
                integration.local_app_data
                == {
                    "data": '{"database": "slurm_acct_db"}',
                    "username": "testuser",
                    "password": "testpassword",
                    "endpoints": "127.0.0.1:3306",
                }
                if good_uri
                else {"data": '{"database": "slurm_acct_db"}'}
            )
        elif leader and not ready:
            assert state.unit_status == ops.BlockedStatus(
                "Waiting for `mysql-proxy-db-uri` secret to be configured"
            )
        else:
            assert mock_charm.unit_status_history == []
