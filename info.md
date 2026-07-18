# Scandia Fireplace

Home Assistant control for **Scandia Aurora electric fireplaces** (36" / 50" /
74"), which are Tuya-based devices.

**Simple sign-in — no developer account, no keys.** You log in the same way as
Home Assistant's official Tuya integration: enter a **user code** from the Smart
Life app and scan a **QR code**. The integration then controls the fireplace
through the Tuya cloud, but with proper fireplace-specific entities:

- **Climate** — power, heat / flame-only mode, target & current temperature, presets
- **Light** — flame on/off, brightness and colour effect
- **Select** — flame animation speed
- **Number** — auto-off countdown timer
- **Switch** — child lock
- **Sensor** — current temperature, plus optional power (W) & energy (kWh)

Function-code mappings are editable from the integration options if your
firmware differs, and a diagnostics download lists the codes your device
reports.
