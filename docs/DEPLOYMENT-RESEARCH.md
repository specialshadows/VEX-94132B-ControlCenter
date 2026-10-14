# Deployment investigation — 14 October 2026

The public [VEX extension repository](https://github.com/VEX-Robotics/vex-vsc-extension) currently exposes README.md and an MIT license, with no extension implementation to inspect. Its README says the source will be open sourced. This is insufficient evidence for embedding an extension or using undocumented internals.

The locally installed extension (0.8.2026020401) has a different **Limited License**. It prohibits standalone redistribution and reverse engineering. This project copies neither its code nor any VEX executable or SDK. Each user supplies an officially installed utility. The public repository's MIT license must not be treated as a license to redistribute the installed binaries. Support/redistribution permission should be obtained from VEX before shipping VEX components with this product.

## What was verified locally

The official, user-installed utility at the VEX extension global storage tools directory executes independently of VS Code. Its `--version --json` reported vexcom **1.0.2b2**, built 30 January 2026. Its own `--help` lists:

```
--write file    Write file to brain
--slot n        slot number (1-8)
--run           Run program after download
--load          Load and Run program
--programs      show programs
--python        Upload python vm to brain
--json          system info in json format
```

Its example explicitly documents `vexcom --slot 2 --write filename serial_port`. The application follows that argument order and passes a `.py` source file. `--run` and `--load` are omitted during upload. Running later uses a separate, explicitly confirmed `--slot n --load serial_port` operation.

`vexcom --usb --json` executed successfully and returned `{"usb":{}}`. This confirms a working no-device scan, not the connected-device schema. The adapter recognizes nested device objects only when `platform` is V5, `device`/`type` is brain, and `communication`/`communication_port` is a nonempty string. Other schemas fail closed and remain visible in Activity. A real connected-device response must be captured to verify this parser. No automatic raw serial-port guessing is used. User terminal and communication ports remain separate.

The existing robot settings declare V5, Python, `src/main.py`, slot 1, SDK `V5_1_0_1_25`. Its main file is self-contained. Preparation parses its syntax without executing it, verifies its hardware and centralized settings, then stages an exact source copy with SHA-256. It does not compile to host Python bytecode, concatenate unknown modules, or install firmware. Actual Python acceptance and VM compatibility remain unverified until a Brain is attached. The adapter is an integration candidate using a real installed utility, not a claim of VEX-supported third-party deployment.

## Verification boundaries

An upload requires a fresh device match, matching source hash, matching utility hash, a slot in 1–8, and user confirmation. Tickets expire after five minutes and cannot be retried. A nonzero exit or timeout is an error, never success. Exit zero reports utility completion; a separate `--programs` query checks that the selected slot is present. This is **not byte-for-byte readback** and does not establish motor behavior. Run remains disabled when slot presence cannot be established.

No Brain was connected during development. Physical USB, Python upload acceptance, program slot inspection, separate load/run behavior, user/communication port naming, VM version handling, and handle contention on Windows remain pending. Update/install the Python VM using official VEXcode or the VEX extension; Control Center does not automatically alter firmware or the VM.

## Architecture decision

[Tauri 2](https://v2.tauri.app/start/prerequisites/) suits a shared Windows/macOS app with a bundled React UI and narrow native commands. Rust owns native folder/file selection and provides trusted filesystem roots. A bundled Python service supplies AST-based edits, Git processes, BMP validation, and vexcom orchestration. It communicates over stdin/stdout with its parent process; there is no local HTTP server, remote shell, token field, CDN editor, or browser-accessible device service. Python is packaged into the application and need not be installed by end users.

VS Code itself is not embedded. The VEX utility is discovered in official global storage or selected through a native file dialog. Native processes are serialized; utility subprocesses have bounded timeouts and no persistent serial handles. Users must close competing VEX sessions; external process locking cannot be guaranteed without testing actual devices.

## Supported fallback

If utility discovery, the connected-device schema, Python preparation, VM compatibility, or upload verification fails, save the actual robot file and open that existing project in the official VEX extension or VEXcode. Select its program slot and download there. This preserves the Brain artwork and existing robot repository. Do not treat Control Center as hardware-verified until the checklist in HARDWARE-TESTING.md passes.

Official references: [V5 Python API](https://api.vex.com/v5/home/python/index.html), [VEX library](https://kb.vex.com/), [REC Foundation Achieve resources](https://kb.roboticseducation.org/hc/en-us/articles/4461386798743-RECF-Achieve-Robotics-Competition-Game-Manual-and-Resources). Competition legality is not inferred from standard V5RC rules.
