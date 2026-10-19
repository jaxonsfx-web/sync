# Sync

A minimal, dark script-editor prototype for macOS-oriented workflows.

## Current status

This repository currently contains the UI prototype only. It supports editing local Lua/Luau text, tabs, opening and saving files, and copying text. The Execute button is intentionally a placeholder; no Roblox attachment, injection, or execution backend is included.

## Preview

Open `preview/index.html` in a browser to try the prototype.

## Safety and scope

- Treat downloaded scripts as untrusted.
- Do not put API keys, tokens, or other secrets in this repository.
- No compiled binaries or third-party executables are included.
- This project does not include a Roblox injection backend.

## Included tools

- `preview/index.html` is a dependency-free browser prototype with local Lua/Luau text editing, syntax coloring, tabs, local file open/save, copy, and basic editor settings. It makes no third-party network requests. The Preview button is intentionally a placeholder and does not execute scripts.
- `tools/validate_offsets.py` checks JSON offset dumps and C/C++ headers for basic formatting, duplicate identifiers, and suspicious numeric ranges. It runs offline and never attaches to or modifies another process. A clean report does **not** prove the values are correct for any specific application build.

Run the validator with Python 3:

```sh
python3 tools/validate_offsets.py path/to/offsets.json
python3 tools/validate_offsets.py path/to/offsets.hpp
```

## Next steps

- Package the editor as a native macOS app after reviewing dependencies and build scripts.
- Add tests for more offset file formats and document the source/version for each dataset.
- Keep updater endpoints and release assets under the project owner's control.

## License

No license has been specified yet. Unless a license is added, normal copyright applies.
