# Lambda Wars Python Integration and `srcbase` Overview

This document explains how Lambda Wars integrates Python with the Source Engine, what the `srcbase` module is, how to explore its API, and practical workflows to develop and debug Python code that depends on the engine (e.g., from PyCharm). It also includes tips to export this document to PDF.

## What is `srcbase`?

- `srcbase` is a Python façade module that re-exports symbols from compiled, engine-backed CPython extensions.
- You can find the stub at:
  - `lambdawars/python/srcbase.py`
    - It imports from `_srcbase` and `_entitiesmisc` (compiled modules shipped with the game).
- These compiled extensions link directly to Source Engine binaries. They only work when loaded inside the game’s embedded Python runtime.

## Where does `import srcbase` resolve from?

- The game sets up `sys.path` so that `lambdawars/python` is importable.
- `import srcbase` → loads `lambdawars/python/srcbase.py`, which re-exports engine symbols from the compiled extensions.
- The compiled modules (e.g., `_srcbase`) are part of the game’s binary distribution (next to engine DLLs) and not available on PyPI.

## Embedded CPython Interpreter

- Lambda Wars embeds CPython inside the engine. Python scripts run within the game process, with full access to engine APIs.
- There is no standalone interpreter in this repo that can import `srcbase` outside the game.
- Attempting to import `_srcbase` from a normal Python shell will fail because engine DLLs and state aren’t present.

## Exploring the API (inside the game)

Use the in-game console to run Python snippets via `py_run`:

```python
# List public names
import srcbase
print("\n".join(sorted(n for n in dir(srcbase) if not n.startswith("_"))))
```

```python
# Inspect docs/types for everything
import srcbase, inspect
for name, obj in inspect.getmembers(srcbase):
    if not name.startswith("_"):
        print(name, "->", type(obj), inspect.getdoc(obj) or "")
```

```python
# Get help on a specific symbol
import srcbase
help(srcbase)
help(srcbase.ConVarRef)  # example
```

Console-friendly examples:

```
py_run "import srcbase; print('\\n'.join(sorted([n for n in dir(srcbase) if not n.startswith('_')])))"
py_run "import srcbase, inspect; print(inspect.getdoc(srcbase.ConVarRef))"
```

## Typical Development Workflow

1. Edit Python files in your editor (e.g., PyCharm/VSCode).
2. Launch the game in developer mode.
3. Use `py_run` to load/execute your Python changes or hot-reload logic that supports it.
4. For advanced debugging, attach a remote debugger (see below).

## Remote Debugging with PyCharm (Attach to Game)

You can debug code inside the game process by attaching PyCharm’s debugger:

1. Ensure `pydevd_pycharm` is importable by the game (place it in a folder on `sys.path`, or vendor it in a package directory the game loads).
2. Start the debug server in PyCharm (Listen for incoming connections on a chosen port, e.g., 5678).
3. From the in-game console:
   ```
   py_run "import pydevd_pycharm; pydevd_pycharm.settrace('127.0.0.1', port=5678, suspend=False)"
   ```
4. Once connected, set breakpoints in your project. Execution in the game will hit them as code runs.

Notes:
- Keep `suspend=False` initially to avoid pausing the render thread at attach time.
- You can use conditional breakpoints and log points to minimize impact on frame time.

## Generating a Local API Index

You can script a quick dump of `srcbase` names and docs to a file for reference. We ship a helper in `lambdawars/python/tools/dump_srcbase_api.py`:

```
py_run "import tools.dump_srcbase_api as dump; dump.dump('srcbase_api_dump.txt')"
```

You can also inline a one-off snippet:

```
py_run "import srcbase, inspect, textwrap, os; p='srcbase_api_dump.txt'; \
with open(p, 'w', encoding='utf-8') as f: \
    for name, obj in sorted(((n, o) for n, o in inspect.getmembers(srcbase) if not n.startswith('_')), key=lambda x: x[0]): \
        f.write(f'{name} :: {type(obj).__name__}\\n'); \
        doc = inspect.getdoc(obj) or ''; \
        if doc: \
            f.write(textwrap.fill(doc, width=100, subsequent_indent='    ') + '\\n'); \
        f.write('\\n'); \
print('Wrote', os.path.abspath(p))"
```

Both write `srcbase_api_dump.txt` in the current working directory (typically the game’s).

## Related Engine Modules to Explore

- `vmath`: Engine math types (Vector, QAngle, etc.)
- `entities`: Entity APIs and wrappers
- `gameinterface`: Engine/game system interfaces
- You can explore them with the same `inspect` techniques as above.

## CPython Version Compatibility

The embedded interpreter targets **CPython 3.3**. Engine-side modules (`_srcbase`, `_entitiesmisc`, etc.) are compiled against that ABI and are not compatible with newer Python versions. Attempting to run the game with a different interpreter will result in import or linker errors. Always match the version expected by the shipped binaries.

## Converting This Document to PDF

Use Pandoc (or any Markdown-to-PDF tool):

```bash
pandoc -s lambdawars/python/docs/engine_python_integration.md -o engine_python_integration.pdf
```

On Windows, install Pandoc from `https://pandoc.org` and run the command in PowerShell from the project root. You can then open or share `engine_python_integration.pdf`.

## FAQ

- “Can I import `srcbase` in a normal Python shell?”  
  No. It depends on engine DLLs and state only available in the running game.

- “Where do I find the authoritative API?”  
  In the compiled modules and engine source that builds them. For Python-level stubs, see `lambdawars/python/srcbase.py` and the docs in `lambdawars/python/docs/library/srcbase.rst`.

- “How do I list all constants/enums?”  
  Use `dir(srcbase)` and print/filter by name patterns, or iterate `inspect.getmembers`.


