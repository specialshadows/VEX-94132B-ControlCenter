# TEST FIXTURE ONLY — DO NOT FLASH. Snapshot of centralized robot schema v2.
# Team 94132B — REC Foundation Achieve / Pinnacle, JROTC
# Original code by E.M.
#
# 2026-2027 competition robot - VEX V5 Python
# Keep this program self-contained for VEXcode V5 deployment.

from vex import *

brain = Brain()
controller_1 = Controller(PRIMARY)

# ============================================================
# Hardware map / gearing
# ============================================================
# 11W motors use 600-RPM blue (6:1) cartridges.
# The two claw motors are 5.5W (fixed ~200 RPM).
# Port 1: V5 Radio (managed by the Brain/controller).
# Port 15: inertial sensor. AI Vision camera is removed.

DRIVE_GEARS = GearSetting.RATIO_6_1
INTAKE_GEARS = GearSetting.RATIO_6_1
PULLEY_GEARS = GearSetting.RATIO_6_1
CLAW_GEARS = GearSetting.RATIO_18_1

# Change reversal flags ONLY after checking real motor directions.
FRONT_LEFT_REVERSED = False
BACK_LEFT_REVERSED = False
FRONT_RIGHT_REVERSED = True
BACK_RIGHT_REVERSED = True

TOP_INTAKE_REVERSED = False
BOTTOM_INTAKE_REVERSED = True

# Both pulley motors start NOT reversed.
# The controller explicitly sends opposite spin directions below.
# If the two shafts do not cooperate mechanically, stop and re-check
# the wiring and reversal settings before further use.
PULLEY_LEFT_REVERSED = False
PULLEY_RIGHT_REVERSED = False

CLAW_ROTATE_REVERSED = False
CLAW_ACTIVATE_REVERSED = False

# ============================================================
# CONTROL CONFIGURATION — edit here, then download this file again.
# No separate runtime imports or Control Center website are required.
# Speeds are commanded percentages, not torque/current limits.
# ============================================================
CONTROL_SCHEMA_VERSION = 2
# Driving direction / joystick tuning (individual motor reversals are above).
# True corrects the reported backwards response without changing steering.
# Verify physical direction with the wheels supported before driving.
DRIVE_FORWARD_REVERSED = True
DRIVE_STEERING_REVERSED = False
DRIVE_SCALE = 0.60
TURN_SCALE = 0.35
DEADZONE = 5

# Reverse drive changes only forward/backward. TOGGLE switches once per tap;
# HOLD is also supported when explicitly selected in the Control Center.
# L2 already lowers the cascade. LEFT is currently unused and avoids a clash.
REVERSE_DRIVE_ENABLED = True
REVERSE_DRIVE_BUTTON = "LEFT"
REVERSE_DRIVE_MODE = "TOGGLE"

# Motor speeds — keep these separate from directions and stopping modes.
INTAKE_SPEED = 50
CASCADE_SPEED = 100
CLAW_ROTATION_SPEED = 25
CLAW_INOUT_SPEED = 20

# Existing claw torque cap is retained for BOTH 5.5W motors.
CLAW_TORQUE_LIMIT = 35
CLAW_HOLD_ENABLED = True
CLAW_HOLD_MODE = "HOLD"
# No feedforward model is validated for this mechanism. Enabling it is rejected.
CLAW_GRAVITY_COMPENSATION_ENABLED = False

# Buttons: R1, R2, L1, L2, UP, DOWN, LEFT, RIGHT, X, B, A, Y.
INTAKE_IN_BUTTON = "R1"
INTAKE_OUT_BUTTON = "R2"
CASCADE_UP_BUTTON = "L1"
CASCADE_DOWN_BUTTON = "L2"
CLAW_ROTATION_UP_BUTTON = "UP"
CLAW_ROTATION_DOWN_BUTTON = "DOWN"
CLAW_INOUT_FORWARD_BUTTON = "X"
CLAW_INOUT_REVERSE_BUTTON = "B"
COFFIN_ZERO_BUTTON = "A"
COFFIN_MAX_BUTTON = "Y"

# Manual directional control only. Automatic endpoints need hardware limits
# and explicit approval; A/Y calibrate the DISPLAY and do not limit travel.
CASCADE_CONTROL_MODE = "TWO_BUTTON_MANUAL"

# Release/idle stopping modes. HOLD is active position holding while powered.
DRIVE_STOPPING = COAST
INTAKE_STOPPING = BRAKE
CASCADE_STOPPING = HOLD
CLAW_INOUT_STOPPING = BRAKE

# Pulley enabled: facing motors receive opposite spin commands below.
# Both facing motors receive opposite spin directions.
PULLEY_ENABLED = True

# Actual V5 controller inputs. Rear mechanical paddles would press one of
# these existing buttons; they do not create additional software inputs.
CONTROLLER_BUTTONS = {
    "R1": controller_1.buttonR1, "R2": controller_1.buttonR2,
    "L1": controller_1.buttonL1, "L2": controller_1.buttonL2,
    "UP": controller_1.buttonUp, "DOWN": controller_1.buttonDown,
    "LEFT": controller_1.buttonLeft, "RIGHT": controller_1.buttonRight,
    "X": controller_1.buttonX, "B": controller_1.buttonB,
    "A": controller_1.buttonA, "Y": controller_1.buttonY,
}

# ============================================================
# Drivetrain - four 11W motors
# ============================================================
front_left = Motor(Ports.PORT14, DRIVE_GEARS, FRONT_LEFT_REVERSED)
back_left = Motor(Ports.PORT13, DRIVE_GEARS, BACK_LEFT_REVERSED)
front_right = Motor(Ports.PORT12, DRIVE_GEARS, FRONT_RIGHT_REVERSED)
back_right = Motor(Ports.PORT11, DRIVE_GEARS, BACK_RIGHT_REVERSED)

left_motors = MotorGroup(front_left, back_left)
right_motors = MotorGroup(front_right, back_right)

# ============================================================
# Intake - two 11W motors
# ============================================================
top_intake = Motor(Ports.PORT8, INTAKE_GEARS, TOP_INTAKE_REVERSED)
bottom_intake = Motor(Ports.PORT20, INTAKE_GEARS, BOTTOM_INTAKE_REVERSED)

# ============================================================
# Pulley / cascade - two 11W motors face each other
# ============================================================
pulley_left = Motor(Ports.PORT9, PULLEY_GEARS, PULLEY_LEFT_REVERSED)
pulley_right = Motor(Ports.PORT2, PULLEY_GEARS, PULLEY_RIGHT_REVERSED)

# ============================================================
# Claw - two 5.5W smart motors
# Motor A (Port 4) rotates the claw to change its angle.
# Motor B (Port 3) drives the claw in/out mechanism.
# ============================================================
claw_rotate = Motor(Ports.PORT4, CLAW_GEARS, CLAW_ROTATE_REVERSED)
claw_activate = Motor(Ports.PORT3, CLAW_GEARS, CLAW_ACTIVATE_REVERSED)

imu = Inertial(Ports.PORT15)


# ============================================================
# Original 94132B dashboard (from src/ui_preview.py)
#
# The V5 Python application is deployed as a single main.py file.
# The UI is copied here, not imported from ui_preview.py, so the
# competition Brain runs it in the SAME program as the controls.
# Only the UI thread may interact with this RobotUI object.
# ============================================================

class RobotUI:
    """One screen owner; callers submit state, then call update from a UI loop.

    No motor commands, calibration, Competition objects, or event callbacks.
    All methods are called by the dedicated UI thread. Robot control callbacks
    only publish their desired mode; the UI thread alone draws to the screens.
    """

    MODES = ("logo", "boot", "auton", "driver", "skills")
    PREFIXES = ("logo", "boot", "auton", "driver", "auton")
    TITLES = {"logo": "TEAM / STANDBY", "boot": "BOOT / STANDBY",
              "auton": "AUTON", "driver": "DRIVER CONTROL",
              "skills": "SKILLS PROGRAMMING"}
    # ASCII punctuation keeps the supplied quote legible on VEX's built-in font.
    QUOTES = ('"baller" - vex commentary', "professional tokyo drifters",
              "try not to get dragged by us", "lowell high school",
              "we meant to do that", "probably tested",
              "totally competition legal", "wheelies are a feature",
              "auton WILL work", "driver diff", "major technical difficulties")

    def __init__(self, brain, controller=None, preview=False):
        self.brain = brain
        self.screen = brain.screen
        self.controller = controller
        self.preview = preview
        self.mode = "boot"
        self.drawn_mode = ""
        self.logs = []
        self.log_dirty = True
        self.motors = (None, None)
        self.drawn_motors = None
        self.pulley_angle = None  # relative motor angle, not absolute lift height
        self.coffin_zero = None
        self.coffin_max = None
        self.drawn_pulley_angle = None
        self.last_update = None
        self.asset_error = None
        self.using_fallback = False
        self.background_ms = 0
        self.skills_selected = False
        self.ticker_offset = 0.0
        self.ticker_text = "    /    ".join(self.QUOTES) + "    /    "
        self.ticker_last = None

    def select_skills(self, selected):
        """UI label selection only. Never starts or changes a robot routine."""
        if self.skills_selected != selected:
            self.skills_selected = selected
            self.drawn_mode = ""

    def competition_mode(self, enabled, autonomous):
        if not enabled:
            return "boot"
        if autonomous:
            return "skills" if self.skills_selected else "auton"
        return "driver"

    def _title(self):
        if self.mode == "boot" and not self.preview:
            return "SKILLS PROGRAMMING / READY" if self.skills_selected else "BOOT / MATCH"
        return self.TITLES[self.mode]

    def _ticker(self, now, force=False):
        if self.ticker_last is not None:
            elapsed = max(0, now - self.ticker_last)
            if not force and elapsed < 40:
                return
            # Advance automatically; drop missed frames rather than blocking.
            self.ticker_offset = (self.ticker_offset + min(elapsed, 200) * 0.05) % (len(self.ticker_text) * 8)
        self.ticker_last = now
        # MONO15 uses an 8-pixel cell. Scroll a bounded text window, keeping
        # every drawing coordinate on screen. No clip-region API is needed.
        offset = int(self.ticker_offset)
        first = offset // 8
        phase = offset % 8
        visible = self.ticker_text[first:first + 58]
        if len(visible) < 58:
            visible += self.ticker_text[:58 - len(visible)]
        strip = Color.RED if self.using_fallback else Color(133, 78, 83)
        self._box(0, 221, 480, 19, strip)
        self._fallback_text(visible, 8 - phase, 235, background=strip)
        # Hide the incoming/outgoing partial character at the strip edges.
        self._box(0, 221, 8, 19, strip)
        self._box(472, 221, 8, 19, strip)

    def set_mode(self, mode: str):
        if mode not in self.MODES:
            raise ValueError("Unknown UI mode")
        self.mode = mode

    def log(self, message):
        # Nine bounded rows fit the original boot/auton log panel.
        for line in str(message).split("\n"):
            self.logs.append(line[:38])
        self.logs = self.logs[-9:]
        self.log_dirty = True

    def set_motor_values(self, left, right):
        """Measured percent velocity, or None if unavailable; never drives motors."""
        self.motors = (left, right)

    def set_pulley_angle(self, degrees, zero=None, maximum=None):
        """Encoder-relative novelty scale; never affects motor commands."""
        self.pulley_angle = degrees
        if zero != self.coffin_zero or maximum != self.coffin_max:
            self.coffin_zero = zero
            self.coffin_max = maximum
            # Force redrawing even if the encoder angle has not changed.
            self.drawn_pulley_angle = None

    def _fake_coffins(self):
        # Display-only 0.0–10.0 novelty scale calibrated by the driver.
        # A sets the lowered position; Y sets the fully raised position.
        if self.pulley_angle is None or self.coffin_zero is None:
            return "ZERO?"
        if self.coffin_max is None:
            return "MAX?"
        travel = self.coffin_max - self.coffin_zero
        if abs(travel) < 30:
            return "MAX?"
        fraction = (self.pulley_angle - self.coffin_zero) / travel
        fraction = max(0.0, min(1.0, fraction))
        return "%.1f" % (fraction * 10.0)

    def _pulley_label(self):
        return "COFFINS TALL*: " + self._fake_coffins()

    def _text(self, value, x, y, font=FontType.MONO15):
        self.screen.set_font(font)
        self.screen.set_pen_color(Color.BLACK)
        self.screen.set_fill_color(Color.WHITE)
        self.screen.print_at(str(value), x=x, y=y)

    def _white(self, x, y, width, height):
        self.screen.set_pen_width(1)
        self.screen.set_pen_color(Color.WHITE)
        self.screen.set_fill_color(Color.WHITE)
        self.screen.draw_rectangle(x, y, width, height)

    def _box(self, x, y, width, height, color):
        self.screen.set_pen_width(1)
        self.screen.set_pen_color(color)
        self.screen.set_fill_color(color)
        self.screen.draw_rectangle(x, y, width, height)

    def _fallback_text(self, text, x, y, font=FontType.MONO15,
                       color=Color.WHITE, background=Color.BLACK):
        self.screen.set_font(font)
        self.screen.set_pen_color(color)
        self.screen.set_fill_color(background)
        self.screen.print_at(text, x=x, y=y)

    def _fallback_background(self):
        # Temporary Persona 5-inspired graphics: native shapes only, no files.
        self.screen.clear_screen(Color.BLACK)
        self._box(0, 0, 9, 216, Color.RED)
        self._box(17, 7, 164, 33, Color.RED)
        self._fallback_text("94132B", 24, 33, FontType.MONO30,
                            background=Color.RED)
        self._fallback_text("UI TEST" if self.preview else "ROBOT STATUS",
                            208, 29)
        self.screen.set_pen_color(Color.RED)
        self.screen.set_pen_width(5)
        for x in (414, 433, 452):
            self.screen.draw_line(x, 7, x - 20, 36)
        self.screen.set_pen_width(1)
        self._box(17, 46, 445, 26, Color.WHITE)
        self._fallback_text(self._title(), 25, 65, color=Color.BLACK,
                            background=Color.WHITE)
        self._box(17, 80, 215, 61, Color.WHITE)
        self._box(247, 80, 215, 61, Color.WHITE)
        for x, label in ((25, "LEFT MOTOR %"), (255, "RIGHT MOTOR %")):
            self._fallback_text(label, x, 92, FontType.MONO12,
                                color=Color.BLACK, background=Color.WHITE)
        self._box(17, 148, 92, 17, Color.RED)
        self._fallback_text("STATUS", 25, 161, FontType.MONO12,
                            background=Color.RED)
        # Right side of STATUS header is reserved for live pulley rotation.
        self._box(0, 221, 480, 19, Color.RED)

    def _fallback_update(self, changed):
        if changed or self.motors != self.drawn_motors:
            for side in range(2):
                x = (25, 255)[side]
                value = self.motors[side]
                self._white(x, 98, 196, 39)
                label = "----" if value is None else "%+04d" % max(-100, min(100, int(value)))
                self._text(label, x, 137, FontType.MONO40)
            self.drawn_motors = self.motors
        if changed or self.pulley_angle != self.drawn_pulley_angle:
            self._box(285, 148, 177, 17, Color.BLACK)
            self._fallback_text(self._pulley_label(), 291, 161,
                                FontType.MONO12)
            self.drawn_pulley_angle = self.pulley_angle
        if self.log_dirty:
            self._box(17, 168, 445, 49, Color.BLACK)
            lines = self.logs[-3:] or ["Screen ready"]
            for row in range(len(lines)):
                self._fallback_text(lines[row], 25, 181 + row * 16)
            self.log_dirty = False

    def _background(self):
        start = self.brain.timer.system()
        self.asset_error = None
        self.using_fallback = False
        self.screen.clear_screen(Color.WHITE)
        prefix = self.PREFIXES[self.MODES.index(self.mode)]
        try:
            card_present = self.brain.sdcard.is_inserted()
        except Exception:
            card_present = False
        if not card_present:
            self.asset_error = "No SD card"
        else:
            # Each BMP: 80x60 = 4,800 pixels and at most 5,878 bytes.
            for tile in range(24):
                filename = "%s%02d.bmp" % (prefix, tile)
                try:
                    ok = self.screen.draw_image_from_file(
                        filename, (tile % 6) * 80, (tile // 6) * 60)
                except Exception:
                    ok = False
                if not ok:
                    self.asset_error = "Missing/bad " + filename
                    break
        if self.asset_error:
            # Replace even partially loaded artwork with a complete usable UI.
            self.using_fallback = True
            self._fallback_background()
        else:
            # All live overlays stay to the right of Ashley's portrait.
            # The team number and decorative eyes belong to the BMP artwork.
            self._box(251, 56, 220, 16, Color.BLACK)
            self._fallback_text(self._title(), 254, 69,
                                FontType.MONO12, color=Color(205, 155, 160))
        self.background_ms = self.brain.timer.system() - start
        self.log_dirty = True
        self.drawn_motors = None
        self.drawn_pulley_angle = None
        self.drawn_mode = self.mode
        if self.controller is not None:
            self.controller.screen.clear_screen()
            self.controller.screen.set_cursor(1, 1)
            self.controller.screen.print("94132B UI TEST" if self.preview else "94132B")
            self.controller.screen.set_cursor(2, 1)
            self.controller.screen.print(self.TITLES[self.mode])

    def update(self, force=False):
        now = self.brain.timer.system()
        changed = self.mode != self.drawn_mode
        if (not force and not changed and self.last_update is not None
                and now - self.last_update < 200):
            self._ticker(now)
            return
        self.last_update = now
        if changed:
            self._background()
        if self.using_fallback:
            self._fallback_update(changed)
            self._ticker(now, force=changed or force)
            return
        cream = Color(241, 224, 204)
        if changed or self.motors != self.drawn_motors:
            # Static labels are baked into the artwork; only the values move.
            # Even +/-100% fits inside each right-hand 105-pixel motor panel.
            for index in range(2):
                x = (256, 369)[index]
                value = self.motors[index]
                self._box(x - 2, 97, 98, 30, Color.BLACK)
                if value is None:
                    number = "----"
                else:
                    number = "%+d%%" % max(-100, min(100, int(value)))
                self._fallback_text(number, x, 122,
                                    FontType.MONO30,
                                    color=cream, background=Color.BLACK)
            self.drawn_motors = self.motors

        if changed or self.log_dirty:
            # Identity remains visible after repeated mode transitions.
            # Logs never overwrite the portrait or displace the driver label.
            self._box(251, 143, 220, 49, Color.BLACK)
            rows = ("DESIGNATED DRIVER: GRAVES",
                    "DRIFTING MODE: TRUE",
                    "MODE: " + ("SKILLS PROGRAMMING" if self.mode == "skills"
                                else self.mode.upper()))
            for row in range(len(rows)):
                self._fallback_text(rows[row], 256, 154 + row * 12,
                                    FontType.MONO12, color=cream)
            if self.preview:
                status = "UI PREVIEW / NO MOTOR CONTROL"
            elif self.mode != "driver":
                status = self.logs[-1] if self.logs else "SCREEN READY"
            else:
                status = ""
            self._fallback_text(status[:34], 256, 190,
                                FontType.MONO12, color=Color(205, 155, 160))
            self.log_dirty = False

        if changed or self.pulley_angle != self.drawn_pulley_angle:
            # Calibrated novelty scale, always marked with an asterisk.
            self._box(400, 196, 70, 22, Color.BLACK)
            self._fallback_text(self._fake_coffins(), 407, 216,
                                FontType.MONO20, color=cream)
            self.drawn_pulley_angle = self.pulley_angle
        self._ticker(now, force=changed or force)
        # No render(): avoid introducing a global double-buffer mode for other code.


# UI state is shared as a simple string; motor control never draws.
UI_REFRESH_MS = 75
ui_mode = "boot"


# ============================================================
# Shared control helpers
# ============================================================
def control_bindings():
    """The active mapping, also suitable for a future desktop config preview."""
    bindings = [
        ("Intake in", INTAKE_IN_BUTTON), ("Intake out", INTAKE_OUT_BUTTON),
        ("Cascade up", CASCADE_UP_BUTTON), ("Cascade down", CASCADE_DOWN_BUTTON),
        ("Claw angle up", CLAW_ROTATION_UP_BUTTON),
        ("Claw angle down", CLAW_ROTATION_DOWN_BUTTON),
        ("Claw in/out forward", CLAW_INOUT_FORWARD_BUTTON),
        ("Claw in/out reverse", CLAW_INOUT_REVERSE_BUTTON),
        ("Display zero", COFFIN_ZERO_BUTTON), ("Display max", COFFIN_MAX_BUTTON),
    ]
    if REVERSE_DRIVE_ENABLED:
        bindings.append(("Reverse drive", REVERSE_DRIVE_BUTTON))
    return bindings


def validate_control_config():
    """Reject conflicts before competition callbacks can command any motors."""
    errors = []
    assigned = {}
    for action, button in control_bindings():
        if not isinstance(button, str) or button not in CONTROLLER_BUTTONS:
            errors.append(action + ": invalid button " + str(button))
        elif button in assigned:
            errors.append(button + ": " + assigned[button] + " / " + action)
        else:
            assigned[button] = action
    if REVERSE_DRIVE_MODE not in ("HOLD", "TOGGLE"):
        errors.append("Reverse drive requires HOLD or TOGGLE mode")
    if (not isinstance(REVERSE_DRIVE_BUTTON, str)
            or REVERSE_DRIVE_BUTTON not in CONTROLLER_BUTTONS):
        errors.append("Reverse drive requires a real V5 button, even when disabled")
    if CLAW_HOLD_MODE != "HOLD":
        errors.append("Claw holding supports HOLD mode only")
    if CLAW_GRAVITY_COMPENSATION_ENABLED is not False:
        errors.append("Gravity compensation is not implemented; leave disabled")
    if CASCADE_CONTROL_MODE != "TWO_BUTTON_MANUAL":
        errors.append("Cascade requires TWO_BUTTON_MANUAL mode")
    for name, value in (("DRIVE_FORWARD_REVERSED", DRIVE_FORWARD_REVERSED),
                        ("DRIVE_STEERING_REVERSED", DRIVE_STEERING_REVERSED),
                        ("REVERSE_DRIVE_ENABLED", REVERSE_DRIVE_ENABLED),
                        ("PULLEY_ENABLED", PULLEY_ENABLED),
                        ("CLAW_HOLD_ENABLED", CLAW_HOLD_ENABLED)):
        if not isinstance(value, bool):
            errors.append(name + " must be True or False")
    for name, value in (("INTAKE_SPEED", INTAKE_SPEED),
                        ("CASCADE_SPEED", CASCADE_SPEED),
                        ("CLAW_ROTATION_SPEED", CLAW_ROTATION_SPEED),
                        ("CLAW_INOUT_SPEED", CLAW_INOUT_SPEED),
                        ("CLAW_TORQUE_LIMIT", CLAW_TORQUE_LIMIT)):
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not 0 <= value <= 100):
            errors.append(name + " must be from 0 to 100")
    for name, value in (("DRIVE_SCALE", DRIVE_SCALE), ("TURN_SCALE", TURN_SCALE)):
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not 0 <= value <= 1):
            errors.append(name + " must be from 0 to 1")
    if (not isinstance(DEADZONE, (int, float)) or isinstance(DEADZONE, bool)
            or not 0 <= DEADZONE <= 100):
        errors.append("DEADZONE must be from 0 to 100")
    for name, value in (("DRIVE_STOPPING", DRIVE_STOPPING),
                        ("INTAKE_STOPPING", INTAKE_STOPPING),
                        ("CASCADE_STOPPING", CASCADE_STOPPING),
                        ("CLAW_INOUT_STOPPING", CLAW_INOUT_STOPPING)):
        if value not in (COAST, BRAKE, HOLD):
            errors.append(name + " must be COAST, BRAKE or HOLD")
    return errors


def button_pressed(name):
    return CONTROLLER_BUTTONS[name].pressing()


reverse_drive_active = False
reverse_drive_previous = False


def reset_reverse_drive():
    """Enter driver control in normal mode; an already-held key is not a tap."""
    global reverse_drive_active, reverse_drive_previous
    reverse_drive_active = False
    reverse_drive_previous = button_pressed(REVERSE_DRIVE_BUTTON)


def update_reverse_drive():
    """Read each press edge once. Steering never uses this state."""
    global reverse_drive_active, reverse_drive_previous
    pressed = button_pressed(REVERSE_DRIVE_BUTTON)
    if not REVERSE_DRIVE_ENABLED:
        reverse_drive_active = False
    elif REVERSE_DRIVE_MODE == "TOGGLE":
        if pressed and not reverse_drive_previous:
            reverse_drive_active = not reverse_drive_active
    else:
        reverse_drive_active = pressed
    reverse_drive_previous = pressed
    return reverse_drive_active


def claw_rotation_stop_mode():
    return HOLD if CLAW_HOLD_ENABLED and CLAW_HOLD_MODE == "HOLD" else BRAKE


def clamp_speed(speed):
    return max(-100, min(100, speed))


def spin_signed(motor, speed, stop_mode=BRAKE):
    speed = clamp_speed(speed)
    if speed > 0:
        motor.spin(FORWARD, speed, PERCENT)
    elif speed < 0:
        motor.spin(REVERSE, -speed, PERCENT)
    else:
        motor.stop(stop_mode)


def two_button_motor(motor, positive, negative, speed, stop_mode=BRAKE):
    if positive and not negative:
        spin_signed(motor, speed, stop_mode)
    elif negative and not positive:
        spin_signed(motor, -speed, stop_mode)
    else:
        motor.stop(stop_mode)


# ============================================================
# Drivetrain - left stick vertical + right stick horizontal
# ============================================================
def drive_control():
    forward = controller_1.axis3.position()
    turn = controller_1.axis1.position()

    if abs(forward) < DEADZONE:
        forward = 0
    if abs(turn) < DEADZONE:
        turn = 0

    if DRIVE_FORWARD_REVERSED:
        forward = -forward
    if update_reverse_drive():
        forward = -forward
    if DRIVE_STEERING_REVERSED:
        turn = -turn

    left = forward * DRIVE_SCALE + turn * TURN_SCALE
    right = forward * DRIVE_SCALE - turn * TURN_SCALE

    spin_signed(left_motors, left, DRIVE_STOPPING)
    spin_signed(right_motors, right, DRIVE_STOPPING)


# ============================================================
# Intake - R1 inward / R2 outward
# ============================================================
def intake_control():
    inward = button_pressed(INTAKE_IN_BUTTON)
    outward = button_pressed(INTAKE_OUT_BUTTON)

    if inward and not outward:
        spin_signed(top_intake, INTAKE_SPEED)
        spin_signed(bottom_intake, INTAKE_SPEED)
    elif outward and not inward:
        spin_signed(top_intake, -INTAKE_SPEED)
        spin_signed(bottom_intake, -INTAKE_SPEED)
    else:
        top_intake.stop(INTAKE_STOPPING)
        bottom_intake.stop(INTAKE_STOPPING)


# Pulley idle state remembers when HOLD was first engaged.
# Repeated stop(HOLD) calls could reset the hold reference while drifting.
pulley_last_action = None
claw_rotation_last_action = None

# UI-only height scale, calibrated manually each time the program restarts.
# These values do NOT control or limit the pulleys.
coffin_zero_angle = None
coffin_max_angle = None
coffin_a_previous = False
coffin_y_previous = False


def coffin_calibration_control():
    """A = lowered zero; Y = fully raised 10.0, with pulley buttons released."""
    global coffin_zero_angle, coffin_max_angle
    global coffin_a_previous, coffin_y_previous

    a_pressed = button_pressed(COFFIN_ZERO_BUTTON)
    y_pressed = button_pressed(COFFIN_MAX_BUTTON)
    # Ignore calibration requests while the pulley is commanded to move,
    # while its encoder still reports motion, or when both keys are down.
    stationary = (not button_pressed(CASCADE_UP_BUTTON)
                  and not button_pressed(CASCADE_DOWN_BUTTON)
                  and abs(pulley_left.velocity(PERCENT)) < 5)
    if stationary and a_pressed and not coffin_a_previous and not y_pressed:
        coffin_zero_angle = pulley_left.position(DEGREES)
        coffin_max_angle = None
    elif (stationary and y_pressed and not coffin_y_previous
          and not a_pressed and coffin_zero_angle is not None):
        proposed = pulley_left.position(DEGREES)
        if abs(proposed - coffin_zero_angle) >= 30:
            coffin_max_angle = proposed

    coffin_a_previous = a_pressed
    coffin_y_previous = y_pressed

# ============================================================
# Pulley - L1 direction A / L2 direction B
#
# The facing motors always get OPPOSITE rotation commands.
# L1: left FORWARD, right REVERSE
# L2: left REVERSE, right FORWARD
# Both pressed or neither pressed: stop both.
# ============================================================
def pulley_control():
    global pulley_last_action

    if not PULLEY_ENABLED:
        if pulley_last_action != "disabled":
            pulley_left.stop(BRAKE)
            pulley_right.stop(BRAKE)
            pulley_last_action = "disabled"
        return

    direction_a = button_pressed(CASCADE_UP_BUTTON)
    direction_b = button_pressed(CASCADE_DOWN_BUTTON)

    if direction_a and not direction_b:
        pulley_left.spin(FORWARD, CASCADE_SPEED, PERCENT)
        pulley_right.spin(REVERSE, CASCADE_SPEED, PERCENT)
        pulley_last_action = "a"
    elif direction_b and not direction_a:
        pulley_left.spin(REVERSE, CASCADE_SPEED, PERCENT)
        pulley_right.spin(FORWARD, CASCADE_SPEED, PERCENT)
        pulley_last_action = "b"
    elif pulley_last_action != "hold":
        # Capture the position only on the transition to stopped.
        pulley_left.stop(CASCADE_STOPPING)
        pulley_right.stop(CASCADE_STOPPING)
        pulley_last_action = "hold"


# ============================================================
# Claw - D-pad up/down changes Motor A's angle; X/B drives Motor B in/out
# ============================================================
def claw_control():
    global claw_rotation_last_action
    up = button_pressed(CLAW_ROTATION_UP_BUTTON)
    down = button_pressed(CLAW_ROTATION_DOWN_BUTTON)
    if up and not down:
        spin_signed(claw_rotate, CLAW_ROTATION_SPEED, claw_rotation_stop_mode())
        claw_rotation_last_action = "moving"
    elif down and not up:
        spin_signed(claw_rotate, -CLAW_ROTATION_SPEED, claw_rotation_stop_mode())
        claw_rotation_last_action = "moving"
    elif claw_rotation_last_action != "hold":
        # Capture the released angle once, rather than repeatedly resetting
        # the hold target while gravity loads the claw. No constant power/PID.
        claw_rotate.stop(claw_rotation_stop_mode())
        claw_rotation_last_action = "hold"
    two_button_motor(
        claw_activate,
        button_pressed(CLAW_INOUT_FORWARD_BUTTON),
        button_pressed(CLAW_INOUT_REVERSE_BUTTON),
        CLAW_INOUT_SPEED,
        CLAW_INOUT_STOPPING
    )


# ============================================================
# Competition lifecycle
# ============================================================
def stop_all():
    global pulley_last_action, claw_rotation_last_action
    left_motors.stop(BRAKE)
    right_motors.stop(BRAKE)
    top_intake.stop(INTAKE_STOPPING)
    bottom_intake.stop(INTAKE_STOPPING)
    pulley_left.stop(CASCADE_STOPPING)
    pulley_right.stop(CASCADE_STOPPING)
    pulley_last_action = "hold"
    claw_rotate.stop(claw_rotation_stop_mode())
    claw_rotation_last_action = "hold"
    claw_activate.stop(CLAW_INOUT_STOPPING)


def pre_auton():
    stop_all()
    brain.screen.clear_screen()
    brain.screen.print_at("94132B 2026-27", x=20, y=35)

    # Keep the robot stationary while calibrating the inertial sensor.
    if imu.installed():
        brain.screen.print_at("Inertial calibrating...", x=20, y=65)
        imu.calibrate()
        while imu.is_calibrating():
            wait(50, MSEC)
        imu.reset_heading()
        brain.screen.print_at("Inertial ready (P15)", x=20, y=95)
    else:
        brain.screen.print_at("Inertial NOT DETECTED (P15)", x=20, y=95)

    brain.screen.print_at("Pulley enabled (L1/L2)", x=20, y=125)


def auton():
    global ui_mode
    ui_mode = "auton"
    # Autonomous deliberately not implemented.
    # Measurements and a tested routine are needed before robot movement.
    stop_all()


def teleop():
    global ui_mode
    ui_mode = "driver"
    reset_reverse_drive()
    while True:
        drive_control()
        intake_control()
        pulley_control()
        claw_control()
        coffin_calibration_control()
        wait(20, MSEC)


# ============================================================
# Screen worker - independent of the 20ms driver-control loop
# ============================================================
def ui_loop():
    # UI controls only the Brain/Controller screens, never the motors.
    # This uses the EXACT artwork loader, fallback and ticker from the
    # existing preview; Brain SD tiles are optional.
    ui = RobotUI(brain, controller_1, preview=False)
    ui.log("94132B 2026-27")
    ui.log("INERTIAL: PORT 15")
    ui.log("DESIGNATED DRIVER: GRAVES")
    ui.log("DRIFTING MODE: TRUE")

    try:
        while True:
            wanted = ui_mode
            if wanted != ui.mode:
                ui.set_mode(wanted)
                ui.log("MODE: " + wanted.upper())

            if wanted == "driver":
                # Actual measured motor velocity, not joystick estimates.
                ui.set_motor_values(
                    left_motors.velocity(PERCENT),
                    right_motors.velocity(PERCENT)
                )
                ui.set_pulley_angle(
                    pulley_left.position(DEGREES),
                    coffin_zero_angle, coffin_max_angle
                )
            else:
                ui.set_motor_values(None, None)
                ui.set_pulley_angle(
                    pulley_left.position(DEGREES),
                    coffin_zero_angle, coffin_max_angle
                )

            ui.update()
            wait(UI_REFRESH_MS, MSEC)
    except Exception as error:
        # A screen/SD drawing issue must never run motor commands.
        # The separate competition callbacks remain unaffected.
        brain.screen.clear_screen()
        brain.screen.print_at("UI error - check VEX logs", x=12, y=40)
        print("94132B UI error:", error)


# Validate before applying editable settings or registering callbacks.
control_errors = validate_control_config()
if control_errors:
    # Use known-safe constants even if a user edited a stop setting incorrectly.
    left_motors.stop(BRAKE)
    right_motors.stop(BRAKE)
    top_intake.stop(BRAKE)
    bottom_intake.stop(BRAKE)
    pulley_left.stop(HOLD)
    pulley_right.stop(HOLD)
    claw_rotate.stop(HOLD)
    claw_activate.stop(BRAKE)
    brain.screen.clear_screen()
    brain.screen.set_font(FontType.MONO12)
    brain.screen.print_at("CONTROL CONFIG ERROR - robot not started", x=12, y=30)
    brain.screen.print_at(control_errors[0][:72], x=12, y=54)
    for control_error in control_errors:
        print("94132B controls:", control_error)
    raise ValueError("Invalid controller configuration")

# Motor stopping and torque limits
left_motors.set_stopping(DRIVE_STOPPING)
right_motors.set_stopping(DRIVE_STOPPING)
top_intake.set_stopping(INTAKE_STOPPING)
bottom_intake.set_stopping(INTAKE_STOPPING)
pulley_left.set_stopping(CASCADE_STOPPING)
pulley_right.set_stopping(CASCADE_STOPPING)
claw_rotate.set_stopping(claw_rotation_stop_mode())
claw_activate.set_stopping(CLAW_INOUT_STOPPING)

claw_rotate.set_max_torque(CLAW_TORQUE_LIMIT, PERCENT)
claw_activate.set_max_torque(CLAW_TORQUE_LIMIT, PERCENT)

comp = Competition(teleop, auton)
pre_auton()

# Start dashboard after calibration so it exclusively owns the screen.
# VEX Thread allows the motor callbacks to keep their own cadence.
ui_thread = Thread(ui_loop)

while True:
    wait(100, MSEC)
