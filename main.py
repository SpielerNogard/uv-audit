# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "uv-audit @ git+https://github.com/SpielerNogard/uv-audit.git@main"
# ]
# ///
import warnings

if __name__ == "__main__":
    from uv_audit import main

    warnings.warn(
        "This script is deprecated. Please use the 'uv-audit' command directly.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    main()
