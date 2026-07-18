# Scandia Fireplace

Local (no-cloud) Home Assistant control for **Scandia Aurora electric
fireplaces** (36" / 50" / 74"), which are Tuya-based devices.

Talks directly to the fireplace over your LAN using the local Tuya protocol,
exposing:

- **Climate** — power, heat / flame-only mode, target & current temperature
- **Light** — flame on/off, brightness and colour effect
- **Select** — flame animation speed
- **Number** — auto-off countdown timer
- **Switch** — child lock

You'll need the fireplace's **IP address**, **Device ID** and **Local Key**
(see the README for how to obtain them with the `tinytuya` wizard). Data-point
mappings are editable from the integration options if your firmware differs.
