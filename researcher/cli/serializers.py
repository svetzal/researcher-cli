"""Re-exports the shared JSON contract for CLI call sites.

The actual serialization logic lives in ``researcher.contracts`` so it can be shared
with the MCP server without the MCP layer importing from ``researcher.cli``. Import
from here (rather than ``researcher.contracts`` directly) is the CLI-layer convention;
both are the same objects.
"""

from researcher.contracts import (
    SearchEnvelope,
    serialize_config,
    serialize_config_path,
    serialize_config_set,
    serialize_empty_search,
    serialize_index_result,
    serialize_init_result,
    serialize_pack_result,
    serialize_repositories,
    serialize_repository,
    serialize_search,
    serialize_status,
    serialize_unpack_result,
)

__all__ = [
    "SearchEnvelope",
    "serialize_config",
    "serialize_config_path",
    "serialize_config_set",
    "serialize_empty_search",
    "serialize_index_result",
    "serialize_init_result",
    "serialize_pack_result",
    "serialize_repositories",
    "serialize_repository",
    "serialize_search",
    "serialize_status",
    "serialize_unpack_result",
]
