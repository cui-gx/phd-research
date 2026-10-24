"""Set process affinity before scientific libraries are imported."""
import os
import sys


def main():
    cpus = [int(v) for v in os.environ.get("P1_CPU_AFFINITY", "").split(",") if v]
    if cpus and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, cpus)
    from .science import main as science_main
    return science_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
