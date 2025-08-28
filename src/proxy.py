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

"""Manage MySQL database proxy operations on machine."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from urllib.parse import ParseResult, urlparse

import ops
from charms.data_platform_libs.v0.data_interfaces import PrematureDataAccessError

from constants import DATABASE_INTEGRATION_NAME, DB_URI_SECRET_KEY, DB_URI_SECRET_LABEL

if TYPE_CHECKING:
    from charm import MySQLProxyCharm


@dataclass(frozen=True)
class DatabaseProxyData:
    """Database info extracted from the configured database URI.

    Attributes:
        username: Username to use when accessing the proxied database.
        password: Password to use when accessing the proxied database.
        endpoints: List of endpoints that can be used to access the proxied database.
    """

    username: str
    password: str
    endpoints: list[str]


def load_database_data(charm: "MySQLProxyCharm") -> DatabaseProxyData:
    """Load proxied MySQL database data from a Juju secret.

    Args:
        charm: Charm to load Juju secret from.

    Raises:
        ValueError:
            Raised if charm cannot access the database URI secret,
            or if the provided database URI is invalid.
    """
    try:
        secret = charm.model.get_secret(
            id=cast(str | None, charm.config.get(DB_URI_SECRET_KEY)),
            label=DB_URI_SECRET_LABEL,
        )
    except (ops.ModelError, ops.SecretNotFoundError):
        raise ValueError(
            "cannot access configured database uri. "
            + f"ensure that database uri secrets exists and model '{charm.model.name}' "
            + "has been granted access to the secret"
        )

    content = secret.get_content(refresh=True)[DB_URI_SECRET_KEY]
    uri = urlparse(content)
    validate_database_uri(uri)
    return DatabaseProxyData(
        username=cast(str, uri.username),  # `ValueError` will be raised `username` is None.
        password=cast(str, uri.password),  # `ValueError` will be raised `username` is None.
        endpoints=[f"{uri.hostname}:{uri.port}"],
    )


def set_database_data(
    charm: "MySQLProxyCharm", data: DatabaseProxyData, /, integration_id: int | None = None
) -> None:
    """Set proxied database data for integrated MySQL clients.

    Args:
        charm: Instance of the charm to access the database integration.
        data: Database proxy data to save to the integrations.
        integration_id: ID of integration to update.
    """
    integrations = charm.mysql.relations
    if integration_id is not None:
        integrations = [charm.mysql.get_relation(DATABASE_INTEGRATION_NAME, integration_id)]

    for integration in integrations:
        try:
            charm.mysql.set_credentials(
                integration.id,
                username=data.username,
                password=data.password,
            )
            charm.mysql.set_endpoints(integration.id, ",".join(data.endpoints))
        except PrematureDataAccessError:
            # Do not set integration data if database has not been requested by a client yet.
            # It's easier to ask the `mysql_client` interface for forgiveness rather than check
            # if the database has been requested by a client each time we call this function.
            pass


def validate_database_uri(data: ParseResult):
    """Validate proxied MySQL database URI.

    Args:
        data: Proxied database data as a parsed URL.

    Raises:
        ValueError: Raised if the provided database URI is invalid.
    """
    missing = []
    if not data.username:
        missing.append("username")
    if not data.password:
        missing.append("password")
    if not data.hostname:
        missing.append("hostname")
    if not data.port:
        missing.append("port")

    if missing:
        raise ValueError(f"missing required component(s) in database uri: {', '.join(missing)}")

    if data.scheme != "mysql":
        raise ValueError(f"invalid scheme '{data.scheme}'. only the 'mysql' scheme is supported")
