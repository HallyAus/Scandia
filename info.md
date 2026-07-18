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

Setup is **cloud-assisted but runs locally**: you enter your Tuya IoT project
credentials once, the integration auto-fetches the fireplace's local key from
the Tuya cloud (and re-fetches it automatically if it ever changes), then
controls the fireplace over your LAN. You only supply the device's **IP
address**. Data-point mappings are editable from the integration options if your
firmware differs.
