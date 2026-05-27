"""Smoke tests that verify the uv_audit package can be imported and is versioned."""


def test_import_uv_audit():
    """Verify that uv_audit can be imported and exposes a non-empty __version__."""
    # arrange / act
    import uv_audit

    # assert
    assert uv_audit.__version__
