# Scandia Fireplace

Home Assistant control for **Scandia Aurora electric fireplaces** (36" / 50" /
74"), which are Tuya-based devices.

**One simple sign-in, your choice of control.** Log in like Home Assistant's
official Tuya integration — enter a **user code** from the Smart Life app and
scan a **QR code**. No developer account or key extraction. That sign-in
retrieves both the cloud token and the device's local key, so you can pick:

- **☁️ Cloud** — control via the Tuya cloud (works anywhere).
- **🏠 Local** — control directly over your LAN (fast, no internet needed); the
  local key is retrieved for you and self-heals if it changes.

Either way you get proper fireplace entities:

- **Climate** — power, heat / flame-only mode, target & current temperature, presets
- **Light** — flame on/off, brightness and colour effect
- **Select** — flame animation speed
- **Number** — auto-off countdown timer
- **Switch** — child lock
- **Sensor** — current temperature, plus optional power (W) & energy (kWh)

Address mappings are editable from the options, and a diagnostics download lists
what your device reports.
