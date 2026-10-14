# Hardware testing status

**Physical verification pending. No robot was connected during implementation.** Automated tests use temporary Git repositories and synthetic process/device responses. They are not hardware tests.

Before operating a competition robot, a human must verify:

- Windows VEX USB driver installation and official utility initialization.
- A USB scan identifies the actual V5 Brain, identity, communication port, and separate user port. Record Activity output if schema is rejected.
- Unplugging the Brain changes connection status. Preparing, uploading, and running fail when the selected device is missing or changed.
- V5 Python VM is installed and compatible using the official VEX tools.
- An existing slot can be deliberately replaced after reviewing the exact destination.
- Upload utility exit zero and subsequent selected-slot presence correspond to an actual accepted Python program. Check the Brain directly.
- Upload never runs the program automatically. The separate Run confirmation starts only the selected slot. A physical observer should be ready to stop the robot.
- Another VEX application holding the connection produces an actionable failure; closing it restores access.
- Drive: ports 14/13 left, 12/11 right, Axis3 forward, Axis1 turn. Hold-to-reverse affects forward only and stops on release.
- Cascade: ports 9/2 receive opposite rotations and cooperate physically; stop immediately if shafts fight. HOLD engages on release. A/Y display references do not provide overtravel protection.
- Claw angle P4 (5.5W) and in/out P3 (5.5W) remain separate. Review HOLD patch and test its thermal/torque behavior. No gravity compensation controller is implemented.
- Preserve the user’s working speed and torque settings, including 100% values. Read the selected local source rather than assuming GitHub main has the newest tuning. Manufacturer current and thermal limits remain active; a 100% command does not bypass them.
- SD tiles load from the card root and preserve the original UI, including missing-card fallback.

Do not enable autonomous travel or assume encoder feedback provides absolute mechanical limits. Firmware changes and VM updates are performed through official VEX tools.

Record the computer OS, utility version, Brain firmware/VM version, USB scan, slot, source SHA-256, observed outcomes, and tester/date before marking any item passed.
