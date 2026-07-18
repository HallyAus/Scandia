# Scandia Fireplace — Home Assistant integration

A [HACS](https://hacs.xyz/) custom integration for **Scandia Aurora electric
fireplaces** (36" / 50" / **74"**). The Scandia Aurora fires are Tuya-based
devices normally controlled from the **Scandia Aurora Wi-Fi** app (a re-branded
Tuya / Smart Life app). This integration brings them into Home Assistant with a
**simple sign-in** — no Tuya developer account, no keys to copy.

You sign in the same way Home Assistant's official Tuya integration does: enter
a short **user code** from the Smart Life app and scan a **QR code**. The
integration then talks to your fireplace through the Tuya cloud, but maps it to
proper, fireplace-specific Home Assistant entities (flame light, flame speed,
presets, timer, child lock) instead of the generic controls the official
integration produces.

> ℹ️ **Cloud vs. local:** the QR sign-in only grants cloud access, so this
> integration controls the fireplace **through Tuya's cloud** (like the official
> Tuya integration). Local-only control is possible but requires a Tuya IoT
> developer project to obtain the device's local key — see
> [Local control](#local-control-alternative).

## Features

Depending on what your fireplace firmware exposes, you get:

| Entity | Platform | What it controls |
| --- | --- | --- |
| Fireplace | `climate` | Power on/off, heat vs. flame-only mode, target & current temperature, heat presets |
| Flame | `light` | Flame on/off, brightness, colour/effect |
| Flame speed | `select` | Flame animation speed |
| Auto-off timer | `number` | Countdown auto-off timer (hours) |
| Child lock | `switch` | Engage/release the child lock |
| Current temperature | `sensor` | Room temperature |
| Power / Energy | `sensor` | Live power (W) and cumulative energy (kWh), if reported |

Entities are created only when the matching Tuya function code is present, so
you won't see controls your unit doesn't support. Flame-specific controls,
presets and the power/energy sensors are **opt-in** — their codes vary between
models, so enable them under **Configure** once you've identified them from the
diagnostics (see [Function codes](#function-codes-advanced)).

## Installation (HACS)

1. In Home Assistant go to **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/HallyAus/Scandia` as an **Integration**.
3. Search for **Scandia Fireplace**, install it, and **restart Home Assistant**.
4. Go to **Settings → Devices & services → Add integration → Scandia Fireplace**.

<details>
<summary>Manual installation</summary>

Copy `custom_components/scandia_fireplace` into your Home Assistant
`config/custom_components/` directory and restart Home Assistant.
</details>

## Setup

Make sure the fireplace is already added to the **Scandia Aurora / Smart Life /
Tuya** app and working there. Then:

**Step 1 — User code**
In the Smart Life app, go to **Me → ⚙ (Settings) → Account and Security →
User Code** and note the code. Enter it in Home Assistant.

**Step 2 — Scan the QR code**
A QR code appears. In the Smart Life app tap **＋ (top right) → Scan**, scan it,
then press **Submit** in Home Assistant to complete the login.

**Step 3 — Select your fireplace**
Pick the fireplace from the list of devices on your account. Done.

> You need a second screen to show the QR code (Home Assistant on a computer)
> while you scan it with the phone running the Smart Life app.

## Function codes (advanced)

Tuya cloud devices expose their functions as named **codes** (e.g. `switch`,
`temp_set`). This integration ships with sensible defaults for a standard
electric-fireplace heater, but the flame-related codes vary between models and
are left disabled until you set them.

If some controls are missing or behave oddly:

1. Go to **Settings → Devices & services → Scandia Fireplace →
   ⋮ → Download diagnostics**. The `status_codes` section lists every function
   code the device currently reports, with its live value.
2. Toggle a function from the fireplace/app and re-download to see which code
   changes.
3. Enter the correct codes under **Configure**. Leave a field blank to disable
   that feature.

### Default code mapping

| Function | Default code |
| --- | --- |
| Power / flame on-off | `switch` |
| Target temperature | `temp_set` |
| Current temperature | `temp_current` |
| Flame brightness | `bright_value` |
| Countdown timer | `countdown_set` |
| Child lock | `child_lock` |
| Heat preset | `mode` |
| Heating element | _unset_ |
| Flame effect / colour | _unset_ |
| Flame speed | _unset_ |
| Power sensor, W | _unset_ |
| Energy sensor, kWh | _unset_ |

## Troubleshooting

- **`login_error`** — double-check the user code (it changes if you log out of
  the app), and make sure you scanned the QR with the **Smart Life / Tuya**
  app, not a generic camera, before pressing Submit. The QR code expires after
  a few minutes; if it does, cancel and start again.
- **No devices found** — confirm the fireplace shows up in the Smart Life app
  under the same account whose user code you used.
- **Entity says re-authentication needed** — the cloud session expired. Follow
  the re-auth prompt to scan a fresh QR code; your settings are kept.
- **Values look wrong / controls missing** — re-map the function codes from
  diagnostics as described above.

## Local control (alternative)

If you specifically want **local** (no-cloud) control, that path exists but
needs the device's *local key*, which requires a one-time free **Tuya IoT
developer project**. Tools like the `tinytuya` wizard or `make-all/tuya-local`
can retrieve it. This integration uses the simpler cloud sign-in by design; open
an issue if you'd like a local-control option added.

## Disclaimer

This is an unofficial, community integration and is not affiliated with or
endorsed by Scandia or Tuya. Electric fireplaces are heating appliances —
always follow the manufacturer's safety guidance and never rely solely on
automation for an unattended appliance.

## License

Released under the [MIT License](LICENSE).
