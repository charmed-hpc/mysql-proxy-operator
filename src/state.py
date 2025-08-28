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

"""Manage the state of the MySQL proxy charmed operation."""

from typing import TYPE_CHECKING, cast

import ops
from hpc_libs.interfaces import ConditionEvaluation

from constants import DB_URI_SECRET_KEY, DB_URI_SECRET_LABEL

if TYPE_CHECKING:
    from charm import MySQLProxyCharm


def db_uri_secret_exists(charm: "MySQLProxyCharm") -> ConditionEvaluation:
    """Check if the `mysql-proxy` secret exists."""
    try:
        charm.model.get_secret(
            id=cast(str | None, charm.config.get(DB_URI_SECRET_KEY)),
            label=DB_URI_SECRET_LABEL,
        )
        exists = True
    except (ops.ModelError, ops.SecretNotFoundError):
        exists = False

    return ConditionEvaluation(
        exists, "Waiting for `mysql-proxy-db-uri` secret to be configured" if not exists else ""
    )


def check_mysql_proxy(charm: "MySQLProxyCharm") -> ops.StatusBase:
    """Determine the state of the MySQL proxy application/unit based on satisfied conditions."""
    ok, message = db_uri_secret_exists(charm)
    if not ok:
        return ops.BlockedStatus(message)

    return ops.ActiveStatus()
