from __future__ import annotations

import sys

from dawocue.app import run_app
from dawocue.frozen_runtime import configure_frozen_numba_cache


configure_frozen_numba_cache()


def main() -> int:
    if "--self-test" in sys.argv:
        from dawocue.self_test import run_self_test

        return run_self_test()

    run_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
