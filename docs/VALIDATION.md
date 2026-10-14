# Validation record

Development date: 14 October 2026. Physical robot/USB verification: **pending**.

Code revision: `c70bf7d355dfd49328fd5206dda5f36f52399253`.

[Verified Desktop builds run](https://github.com/specialshadows/94132B-Control-Center/actions/runs/38609441678).

| Platform | Service tests | Packaged service | Desktop build / installers | Result |
| --- | --- | --- | --- | --- |
| Windows x64 | 19 passed | Built | NSIS EXE, MSI, portable ZIP | Success |
| macOS Apple Silicon | 19 passed | Built | App and DMG | Success |
| macOS Intel | 19 passed | Built | App and DMG | Success |

All three jobs completed successfully. These are unsigned development packages; production code signing and Apple notarization are not configured. Build success does not establish installed-GUI or hardware operation on every target OS version.

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
