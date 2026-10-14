# 94132B Control Center

Cross-platform desktop development app for Lowell High School Team 94132B. Near-black and muted green game-menu interface, cream text, Gothic typography, and offline Python editing. Design inspired by TCOAAL; no game artwork is redistributed.

**GITHUB → CONFIGURE → FLASH TO BRAIN**

The robot repository remains separate at `specialshadows/94132B`. This repository contains the desktop app only. No robot code is rewritten until the user reviews and confirms a specific local save. Nothing is pushed or run automatically.

## Use

See [Windows quick start](docs/WINDOWS-QUICKSTART.md), [deployment investigation](docs/DEPLOYMENT-RESEARCH.md), and [hardware checklist](docs/HARDWARE-TESTING.md).

Download installers from a successful **Desktop builds** GitHub Actions run. Windows produces NSIS/MSI plus a portable ZIP. macOS produces a metadata-preserving app ZIP and DMG for the runner architecture. Open the DMG and copy the app to Applications, or extract the inner app ZIP. From 0.1.1 the complete macOS bundle and helper are ad-hoc signed and verified before packaging, including an archive extraction check. These development builds are not Apple-notarized; Gatekeeper may require Open Anyway in Privacy & Security for a trusted download. Windows builds remain unsigned. Hardened runtime is disabled for ad-hoc development because the packaged Python helper loads extracted libraries without a Developer ID team identity. Production distribution requires Apple Developer ID signing, hardened runtime/notarization, and signing of the embedded service; Windows production installers should be Authenticode signed. Signing certificates are not included in this repository.

Prerequisites to run: Git and a configured credential helper (Git Credential Manager or GitHub CLI), officially installed VEX vexcom/USB drivers, and a compatible Python VM on the Brain. Windows also needs WebView2. macOS may require Rosetta if the supplied VEX utility is Intel-only; utility execution is checked and errors are shown. End users do not need Node, Rust, or Python.

## Features implemented

- Native folder/tool selection and narrow Tauri commands; no public local server or unrestricted shell API.
- Secure GitHub device sign-in through GitHub CLI; credentials remain in its OS credential store. Existing Git Credential Manager authentication also works. Clone existing GitHub repositories, branch/commit/status/diff, fast-forward pull, explicit file commits, separately confirmed push, stash/list/restore. Conflicts remain visible and editable; no discard, reset, merge automation, or force push.
- Interactive controller button diagram, assignment dropdowns, presets that include reverse button/mode/enabled settings, reset to loaded values, conflict checks including reverse drive, and locally saved paddle aliases.
- Existing centralized Python literal settings edited using AST source ranges, with exact change preview, source hash checks, and original-file backups. The centralized v2 robot configuration supports D-pad Left toggle reverse by default, optional hold mode, and claw-angle HOLD. Older files retain the guarded legacy adapter. Drive and steering remain separate. The Brain UI is preserved.
- Dedicated drive/intake/cascade/claw pages, fixed hardware validation, 0–100% ranges that preserve existing speed/torque values, and explicit absent-travel-limit/gravity-compensation status.
- Offline Monaco Python editor with syntax highlighting, line numbers, search, dirty indicator, file navigation, syntax diagnostics, and confirmed saves. Robot code is parsed, never executed on the host. Multi-file Python bundling and VEX API semantic type-checking are not implemented.
- Real installed-vexcom discovery/utility checks, direct-device scan, slot selection, exact program staging, reviewed upload, actual process results, post-upload slot presence check, and separately confirmed run.
- BMP tile inspection/preview, missing-tile checks, format/dimension validation, and confirmed copy with byte verification to a user-selected mounted SD folder.
- Cross-platform GitHub Actions packaging and source/dependency locks.

**Hardware integration is not yet physically verified.** The connected-device parser and direct `.py` upload acceptance need a real Brain test. Unknown device schemas block flashing and fall back to the official VEX tools. Slot listing is presence verification, not byte-for-byte program readback. Firmware, Python VM updates, automatic travel, continuous-power gravity compensation, and certification of competition legality are deliberately outside this adapter.

## Build from source

Install Node 24, pnpm 11.25.0, Rust stable and Tauri platform prerequisites, Python 3.12, and native build tools. On macOS use Xcode command-line tools; on Windows install the C++ build tools. Then:

```
pnpm install --frozen-lockfile
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
python scripts/build_service.py
pnpm tauri build
```

For development, prepare the service once, then `pnpm tauri dev`. Development invokes `python3` (`python` on Windows), optionally overridden by `CC_BACKEND_PYTHON`. Production invokes only the packaged executable beside the app. No extra Python installation is needed in a release build.

Config and file backups are stored in the OS application-data directory for `org.lowell.94132b.controlcenter`. Folder and utility selections persist there. No token is stored by this app. Mechanical paddle labels stay in local webview storage.

## Limits and support

The structured adapter targets the current 94132B `src/main.py` layout. Unexpected structures, hardware ports, syntax, or unsupported manifests fail with an explanation instead of rewriting unknown code. Use the editor or official VEX tools for other projects. Git commits refuse pre-existing staged files and obvious secret patterns; users still need to review their exact selected files. SD validation targets the existing 96-tile 80×60 layout, not every possible VEX image format.

Build status must be read from actual Actions runs; workflow files alone do not establish success. Automated tests explicitly use synthetic devices and temporary repositories. See [VALIDATION.md](docs/VALIDATION.md) for recorded outcomes.

## Version 0.1.3 — reverse toggle and claw holding

Use the robot development branch `codex/94132b-control-improvements` and the Control Center branch `codex/reverse-toggle-claw-hold`. The app reads and writes the actual centralized `src/main.py` literals, with no separate deployment configuration. D-pad Left defaults to Toggle Reverse Drive; HOLD mode and feature disable are also available. Port 4 holding and rotation speed reflect the real program, while unimplemented gravity compensation cannot be enabled. Torque increases require an explicit heating/force warning approval. See [configuration sync and testing](docs/CONTROL-SYNC.md).
