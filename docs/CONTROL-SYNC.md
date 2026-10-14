# Reverse-drive and claw settings — version 0.1.3

The robot and app remain separate repositories. The robot's **actual Python
source** is the saved/deployed configuration. Both repositories now contain the
validated changes on `main`, merged with explicit user approval. Nothing was
flashed. Download the app from [GitHub Releases](https://github.com/specialshadows/VEX-94132B-ControlCenter/releases/latest).

The app reads centralized schema v2 in `src/main.py`, validates the motor ports,
and changes literal values using source ranges. It does not execute the robot
program. The reviewed save preserves functions and artwork and backs up the
original file. A stale source hash blocks saving.

## Reverse driving

Default: **D-pad Left → Toggle Reverse Drive**. The controller diagram includes
the current assignment in each button's label/tooltip. Controller and Drivetrain
pages expose the reverse button, feature enabled/disabled and Toggle/Hold mode.

Toggle changes only forward/back on a new press edge, remains selected after
release, and changes back on the next tap. Holding a button cannot repeat toggles.
The robot enters each driver-control period in normal mode and ignores an
already-held button until released and pressed again. Steering remains independent.
Hold mode restores normal direction on release. Normal direction also depends on
the separate `DRIVE_FORWARD_REVERSED` hardware-orientation setting.

The cascade remains L1/L2. A reverse binding that conflicts with any active
mechanism binding is shown by the app and rejected before saving. Disabled
reverse does not occupy its button. Presets save reverse button, mode and enabled
state alongside action mappings; speed and torque values remain as loaded.
Older mapping-only presets retain the loaded reverse settings. Loading any preset
changes the preview until explicitly reviewed/saved; it does not upload or run.

## Claw

Motor A, Port 4, is rotation. Motor B, Port 3, is in/out. The app uses the robot's
`CLAW_ROTATION_SPEED`, `CLAW_INOUT_SPEED`, `CLAW_HOLD_ENABLED` and
`CLAW_HOLD_MODE` values. Disabling active holding requests BRAKE; enabling it
requests the built-in HOLD at the released angle once per stop. Motor B remains
BRAKE. Gravity compensation is displayed as disabled/unimplemented and cannot
be activated through a pretend setting.

The user explicitly approved 100% claw torque allowance on October 14. The app
reads that value from the robot source; rotation/in-out speeds remain 25%/20%.
Any later increase from a lowered value still receives the reviewed heating/force warning.
HOLD sufficiency requires a supported physical test. The encoder is motor
rotation, not an established absolute claw-angle sensor; feedforward/PID tuning
is deferred pending gearing, reference, load and drift measurements.

## Exact deployment source

The selected robot folder was `/Users/hikaru/Documents/94132B`, a second checkout
of the same robot repository. It has been updated to the merged `main` program
so configuration and deployment use the current code. No duplicate project is created. On another computer,
select your existing robot checkout and pull the latest `main`.

The preparation step reads the saved `src/main.py`, validates its configuration,
and stages its exact bytes and SHA-256 hash. Changing the source or staged bytes
invalidates an upload review. Upload and run remain separate confirmed actions.
Save the configuration/editor buffer before preparing. Opening the old installed
0.1.2 app will not provide the new adapter; use the 0.1.3 build.

## Validation

Tests cover canonical read/save/reload, backing up and preserving runtime/UI
functions, uppercase robot button constants versus readable app labels, conflicts,
toggle/hold persistence, torque approval, presets and exact deployment bytes.
Robot tests separately exercise edge detection, steering independence, both
cascade directions and HOLD, claw commands/release, existing mechanisms and UI.
Device results use synthetic inputs only. No physical robot/USB test occurred.

For hardware, support the claw/lift and lift the drive wheels. Check normal
driving first, then a Left tap/hold/release/second tap and steering in both modes.
Check L1/L2, release HOLD, and both claw functions. Watch for sag and heating.
There are **no software cascade travel limits**; A/Y references only the display.
