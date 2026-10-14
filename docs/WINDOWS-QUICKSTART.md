# Windows 10/11

**Select your existing robot checkout.** The current approved robot defaults use 100% claw torque allowance, 25% claw-angle speed, 20% claw in/out speed, and D-pad Left toggle reverse. Control Center reads the actual selected `src/main.py`; it does not replace these with a separate configuration. Review local changes before pulling.

1. Download `94132B-ControlCenter-Windows-x64-Setup.exe` from [the latest GitHub Release](https://github.com/specialshadows/VEX-94132B-ControlCenter/releases/latest). Use version **0.1.5 or later** for the Windows discovery fix. Sign into GitHub with an account that can access the repository. The `.exe` installs the app and bundled service and provides its shortcut. Close the existing app before installing an update.
2. Install Git for Windows (includes Git Credential Manager), GitHub CLI if using the in-app sign-in, and Microsoft Edge WebView2 if absent. Initialize the official VEX VS Code extension once so its vexcom utility and VEX USB drivers are installed. No Python or Node installation is needed to run a packaged Control Center.
3. Open Control Center → GITHUB. Choose your existing robot checkout, or choose a new empty folder and clone `https://github.com/specialshadows/94132B.git`. Sign in through the system browser/device code, then refresh status. Never paste credentials into robot code.
4. Open CONTROLLER or a motor page → LOAD FROM ROBOT FILE. Make changes, preview the exact Python diff, and confirm saving. The original source is backed up in the app data folder. The existing Brain artwork is preserved.
5. Connect and power the actual V5 Brain over USB. Close competing VEXcode/VS Code device connections. In VEX BRAIN, CHECK VEX UTILITY and SCAN FOR V5 BRAIN. If automatic discovery fails, SETTINGS → CHOOSE INSTALLED VEXCOM.
6. Confirm the displayed Brain identity and communication port. Choose slot 1–8. The Brain must already have a compatible Python VM installed through official VEX tools.
7. PREPARE PROGRAM → FLASH TO BRAIN → review destination and confirm. Read the actual utility output and slot verification result. Nothing is automatically run.
8. When the robot area is clear, separately confirm RUN PROGRAM only after a verified upload. Observe the Brain and robot directly. Physical verification has not yet been performed by this project.

If discovery reports an unfamiliar device schema or Python upload fails, use the official VEX extension/VEXcode with the same saved `src/main.py` and selected slot. Expand **SCAN DIAGNOSTICS** on the VEX BRAIN page and copy its contents when reporting a detection failure. A COM port opening/closing in VS Code confirms that Windows sees a serial interface; Control Center identifies the upload interface by hardware ID rather than hard-coding that COM number. Hardware integration is pending until the hardware checklist is completed.

The development installers are unsigned. Windows SmartScreen may identify them as unrecognized; verify that your download came from your own private repository and a successful Actions run. A downloaded artifact is not evidence of a completed hardware test.

## Future updates

After the one-time 0.1.5 installation, click **CHECK FOR UPDATES** in the app header or Settings. If a newer Windows release exists, choose **DOWNLOAD UPDATE**, then **INSTALL UPDATE / CLOSE APP** after saving any edits. Complete the installer and reopen Control Center. Downloads and checksum checks happen inside the app; no browser download or GitHub sign-in is required. Installation is interactive and never flashes the Brain.
