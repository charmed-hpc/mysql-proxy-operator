#!/usr/bin/env just --justfile
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

uv := require("uv")

project_dir := justfile_directory()
src_dir := project_dir / "src"
tests_dir := project_dir / "tests"

export PY_COLORS := "1"
export PYTHONBREAKPOINT := "pdb.set_trace"
export PYTHONPATH := project_dir / "src" + ":" + project_dir / "lib"

uv_run := "uv run --frozen --extra dev"

[private]
default:
    @just help

# Regenerate uv.lock
[group("dev")]
lock:
    uv lock

# Create a development environment
[group("dev")]
env: lock
    uv sync --extra dev

# Upgrade uv.lock with the latest dependencies
[group("dev")]
upgrade:
    uv lock --upgrade

# Generate publishing token for Charmhub
[group("dev")]
generate-token:
    charmcraft login \
        --export=.charmhub.secret \
        --charm=database-proxy \
        --permission=package-manage-metadata \
        --permission=package-manage-releases \
        --permission=package-manage-revisions \
        --permission=package-view-metadata \
        --permission=package-view-releases \
        --permission=package-view-revisions \
        --ttl=31536000  # 365 days

# Apply coding style standards to code
[group("lint")]
fmt: lock
    {{uv_run}} ruff format {{src_dir}} {{tests_dir}}
    {{uv_run}} ruff check --fix {{src_dir}} {{tests_dir}}

# Check code against coding style standards
[group("lint")]
lint: lock
    {{uv_run}} codespell {{src_dir}}
    {{uv_run}} ruff check {{src_dir}}

# Run static type checker on code
[group("lint")]
typecheck: lock
    {{uv_run}} pyright

# Run inclusive naming check on code
[group("lint")]
woke:
    woke {{src_dir}} {{tests_dir}}

# Run unit tests
[group("test")]
unit *args: lock
    {{uv_run}} coverage run \
        --source {{src_dir}} \
        -m pytest \
        --tb native \
        -v -s {{args}} {{tests_dir / "unit"}}
    {{uv_run}} coverage report
    {{uv_run}} coverage xml -o {{project_dir / "cover" / "coverage.xml"}}

# Run integration tests
[group("test")]
integration *args: lock
    #!/usr/bin/env bash
    set -euxo pipefail

    charmcraft -v pack
    mv mysql-proxy_*.charm mysql-proxy.charm
    export LOCAL_MYSQL_PROXY={{project_dir / "mysql-proxy.charm"}}
    {{uv_run}} pytest \
        -v \
        --tb native \
        -s \
        --log-cli-level=INFO \
        {{args}} \
        {{tests_dir / "integration"}}

# Show available recipes
help:
    @just --list --unsorted