import uuid

from uv_audit.environment_handler import EnvironmentHandler


def test_environment_handler_init_folder_uses_tmp_prefix_and_uuid():
    # arrange / act
    handler = EnvironmentHandler()

    # assert
    assert handler._folder.startswith("/tmp/")
    suffix = handler._folder.removeprefix("/tmp/")
    uuid.UUID(suffix)  # raises ValueError if not a valid UUID
