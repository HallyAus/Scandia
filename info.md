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

- **Switch** — master power
- **Buttons** — one per preset: every flame colour, fuel-bed/ember colour and top-light colour
- **Select** — heater (Off/Low/High) and countdown timer (Off/1h–6h)
- **Sensor** — the currently selected flame / log / top-light colour, plus auto-discovered raw endpoints

**Works with rebadges too.** The Aurora is a widely rebranded Tuya OEM
fireplace — Benrocks, Yacoiel, Velaychimney, Auchsiag, Mystflame and many
unbranded inserts use the same board. Pick a **device profile** at setup, and
remap any differing data points from the options. A diagnostics download lists
everything your device reports.
