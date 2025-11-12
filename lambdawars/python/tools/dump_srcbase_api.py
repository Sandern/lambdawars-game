# Utility script to dump the srcbase API when running inside the Lambda Wars game.
# Usage from the in-game console:
#   py_run "import tools.dump_srcbase_api as d; d.dump('srcbase_api_dump.txt')"
#
# The script must run inside the embedded interpreter so that `srcbase`
# (and its compiled engine modules) are available.

import inspect
import os
import textwrap


def dump(filename="srcbase_api_dump.txt"):
    """Dump a formatted list of srcbase names and docs to ``filename``."""
    import srcbase  # only works inside the game runtime

    path = os.path.abspath(filename)
    with open(path, "w", encoding="utf-8") as f:
        for name, obj in sorted(
            (
                (n, o)
                for n, o in inspect.getmembers(srcbase)
                if not n.startswith("_")
            ),
            key=lambda x: x[0],
        ):
            f.write(f"{name} :: {type(obj).__name__}\n")
            doc = inspect.getdoc(obj) or ""
            if doc:
                f.write(textwrap.fill(doc, width=100, subsequent_indent="    "))
                f.write("\n")
            f.write("\n")
    print(f"Wrote {path}")


if __name__ == "__main__":
    dump()

