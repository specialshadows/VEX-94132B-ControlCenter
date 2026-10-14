# Windows 10/11 — later today

1. Download the Windows installer from the private Control Center repository's latest successful **Desktop builds** Actions run. Sign into GitHub with an account that can access the repository. The NSIS `.exe` installs the app and provides its shortcut; alternatively extract the portable ZIP and keep both executables together.
2. Install Git for Windows (includes Git Credential Manager), GitHub CLI if using the in-app sign-in, and Microsoft Edge WebView2 if absent. Initialize the official VEX VS Code extension once so its vexcom utility and VEX USB drivers are installed. No Python or Node installation is needed to run a packaged Control Center.
3. Open Control Center → GITHUB. Choose your existing robot checkout, or choose a new empty folder and clone `https://github.com/specialshadows/94132B.git`. Sign in through the system browser/device code, then refresh status. Never paste credentials into robot code.
4. Open CONTROLLER or a motor page → LOAD FROM ROBOT FILE. Make changes, preview the exact Python diff, and confirm saving. The original source is backed up in the app data folder. The existing Brain artwork is preserved.
5. Later, connect and power the actual V5 Brain over USB. Close competing VEXcode/VS Code device connections. In VEX BRAIN, CHECK VEX UTILITY and SCAN FOR V5 BRAIN. If automatic discovery fails, SETTINGS → CHOOSE INSTALLED VEXCOM.
6. Confirm the displayed Brain identity and communication port. Choose slot 1–8. The Brain must already have a compatible Python VM installed through official VEX tools.
7. PREPARE PROGRAM → FLASH TO BRAIN → review destination and confirm. Read the actual utility output and slot verification result. Nothing is automatically run.
8. When the robot area is clear, separately confirm RUN PROGRAM only after a verified upload. Observe the Brain and robot directly. Physical verification has not yet been performed by this project.

If discovery reports an unfamiliar device schema or Python upload fails, use the official VEX extension/VEXcode with the same saved `src/main.py` and selected slot. Activity contains the real tool output. Hardware integration is pending until the hardware checklist is completed.

The development installers are unsigned. Windows SmartScreen may identify them as unrecognized; verify that your download came from your own private repository and a successful Actions run. A downloaded artifact is not evidence of a completed hardware test.
