# Validation record

Development date: 14 October 2026. Physical robot/USB verification: **pending**.

Code revision: `c70bf7d355dfd49328fd5206dda5f36f52399253`.

[Verified Desktop builds run](https://github.com/specialshadows/94132B-Control-Center/actions/runs/38609441678).

| Platform | Service tests | Packaged service | Desktop build / installers | Result |
| --- | --- | --- | --- | --- |
| Windows x64 | 19 passed | Built | NSIS EXE, MSI, portable ZIP | Success |
| macOS Apple Silicon | 19 passed | Built | App and DMG | Success |
| macOS Intel | 19 passed | Built | App and DMG | Success |

All three jobs completed successfully, but installing the 0.1.0 macOS download subsequently exposed an incomplete bundle signature: `code has no resources but signature indicates they must be present`. Those older macOS artifacts should not be used. Build success alone did not establish installation success.

Version 0.1.1 configures full ad-hoc signing of the macOS app and helper. Hardened runtime is disabled for this development identity because the PyInstaller helper loads extracted Python libraries without a Developer ID team identity. CI now verifies the full signature, executes the signed packaged helper, and verifies the app again after ZIP extraction. macOS artifacts contain a metadata-preserving inner ZIP instead of a raw `.app`. Apple notarization and Windows Authenticode signing are not configured. A browser-downloaded macOS development build can still require user approval in Privacy & Security.

Version 0.1.1 local Apple Silicon repair checks: strict deep signature verification passed before packaging, after ZIP extraction, and after installation in `/Applications`. The signed packaged helper returned `{"ok":true,"result":[]}` for a syntax-check smoke test. The newly installed application launched successfully and its native process was observed running; a complete GUI walkthrough and USB hardware test remain pending. The broken 0.1.0 installation was preserved under local `artifacts/installation-backups/` before replacement. No quarantine attributes were removed and no global Gatekeeper settings were changed.

## Additional checks actually performed

- Local TypeScript checking, production frontend build, Rust native compile check, and packaged Apple Silicon application build passed. Monaco and the Gothic font are bundled locally.
- Packaged local service executed successfully outside the restricted development sandbox, found the installed VEX utility, reported version `1.0.2b2`, and returned the real empty USB scan `{"usb":{}}`. No Brain was connected.
- Browser preview navigation and offline Monaco rendering were inspected; the editor loaded without captured console warnings/errors at that check. Browser-only native actions returned a clear error rather than simulated results. A full native GUI walkthrough was not completed.
- The current private robot `src/main.py` was inspected through the GitHub connector. Configuration parsing and exact HOLD/reverse previews were checked against a separate temporary snapshot. The original robot repository was not modified.
- Synthetic integration tests use temporary real Git repositories and exercise guarded saves/backups, preservation of Brain UI text, simultaneous button swaps and calibration guards, invalid ports, conflicts, reverse-input steering separation, dirty-pull protection, selected-file commits, unstaging without discarding work, repeated HOLD toggling, BMP copying/truncation rejection, deployment argument construction and failure handling, and redaction.
- The 100% preservation regression loads 100 for all four mechanism speeds and claw torque, remaps controller buttons, saves, and checks that every speed and torque literal remains 100. Mapping presets contain buttons only. Percent values remain within 0–100; manufacturer protections are not bypassed.

## Pending / unsupported verification

Connected-device discovery schema, communication/user port identification on actual hardware, Python VM compatibility, actual `.py` upload acceptance, selected-slot inspection, separate Run behavior, contention with other VEX apps, and real motor operation remain unverified. Slot-list presence is not byte-for-byte program readback. Firmware and VM installation remain with official VEX tools. No continuous-power gravity controller, automatic endpoint travel, multi-file Python bundler, or VEX API semantic type checker is provided.

The inspected GitHub robot branch still contained older tuning (50/100/25/20 mechanism speeds and 35 claw torque). The user's working 100/100 revision was not found on that branch. Select the actual working local checkout and preserve it; no attempt was made to change either version or reconcile them automatically.

See [HARDWARE-TESTING.md](HARDWARE-TESTING.md) for the physical checklist and [WINDOWS-QUICKSTART.md](WINDOWS-QUICKSTART.md) for installation and the later USB session.

## Controller layout update (0.1.2)

Replaced the rectangular button grid with a V5-shaped controller: two upper sticks, a lower left directional diamond, X/Y/A/B in the physical V5 diamond, and paired shoulder buttons. The existing selection callback and assignments are preserved. TypeScript/production frontend build passed. An isolated browser render of the actual component was visually checked at 800px and 430px viewport widths; all 12 button targets were clicked and their selected state checked. No robot configuration, speed, or torque data was changed.

## Reverse toggle and claw holding (0.1.3, October 14, 2026)

- Robot development commit `2c595041590d8ab76759fd658fd0f80077ff5792` passed 38
  control/UI host tests and source compilation. The Brain UI, ports, reversal
  flags, torque cap, autonomous function and single Competition object are protected.
- Control Center passed 25 Python service tests plus 3 controller/preset tests,
  TypeScript checking, production frontend build, and the local ARM64 Mac app build.
- Centralized v2 read/save/reload tests preserve runtime functions and stage the
  exact saved Python bytes. Changed files invalidate deployment review. Tests cover
  both toggle/hold modes, conflicts, disabled reverse, backups, presets, and explicit
  torque-increase approval. All USB/deployment process inputs remain synthetic.
- The packaged signed helper read the actual selected `/Users/hikaru/Documents/94132B`
  checkout on the updated robot branch and returned Left/TOGGLE, Port 4 holding,
  25% rotation, 20% in/out and the retained 35% torque cap.
- The complete Mac app passed strict deep signature verification and was installed
  in `/Applications`, preserving the earlier 0.1.2 app under local installation backups.
  Native UI inspection confirmed version 0.1.3, the Left toggle assignment, mode selector,
  claw HOLD checkbox, speeds/torque values and disabled gravity-compensation status.
- The new local Mac ZIP is `artifacts/94132B-Control-Center-0.1.3-macOS-arm64.zip`.
  New Windows/Intel installers and real Brain/USB tests have not been validated
  by this local run. Earlier platform results above apply only to their named revisions.

The normal-drive sign still needs a physical direction check. Claw HOLD strength
cannot be inferred from command tests; the existing 35% cap, load, gearing, binding,
slip and thermal state may affect it. No torque increase, feedforward, custom PID,
automatic cascade endpoints or software travel limiter was added. No robot was flashed.
