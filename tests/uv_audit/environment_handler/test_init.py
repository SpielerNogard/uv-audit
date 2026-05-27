"""Tests for EnvironmentHandler.__init__, verifying the generated temp folder path format."""

import uuid

from uv_audit.environment_handler import EnvironmentHandler


def test_environment_handler_init_folder_uses_tmp_prefix_and_uuid():
    """Ensure the handler's _folder is a /tmp/<UUID> path with a valid UUID suffix."""
    # arrange / act
    handler = EnvironmentHandler()

    # assert
    assert handler._folder.startswith("/tmp/")
    suffix = handler._folder.removeprefix("/tmp/")
    uuid.UUID(suffix)  # raises ValueError if not a valid UUID
