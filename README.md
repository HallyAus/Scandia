# Scandia Fireplace — Home Assistant integration

A [HACS](https://hacs.xyz/) custom integration that brings **Scandia Aurora
electric fireplaces** (36" / 50" / **74"**) into Home Assistant **without the
cloud**. It talks to the fireplace directly over your LAN using the local Tuya
protocol, so control stays fast and keeps working even if the internet — or
Tuya's servers — are down.

The Scandia Aurora fires are Tuya-based devices that you normally control from
the **Scandia Aurora Wi-Fi** app (a re-branded Tuya/Smart Life app). This
integration replaces that app for day-to-day control inside Home Assistant.

> ℹ️ You still pair the fireplace with the Tuya/Smart Life app **once** to
> obtain its credentials (Device ID + Local Key). After that, everything runs
> locally.

## Features

Depending on what your fireplace firmware exposes, you get:

| Entity | Platform | What it controls |
| --- | --- | --- |
| Fireplace | `climate` | Power on/off, heat vs. flame-only mode, target & current temperature |
| Flame | `light` | Flame on/off, brightness, colour/effect |
| Flame speed | `select` | Flame animation speed |
| Auto-off timer | `number` | Countdown auto-off timer (hours) |
| Child lock | `switch` | Engage/release the child lock |

Entities are created only when the matching data point is configured, so you
won't see controls your unit doesn't support.

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

## What you need before adding it

Local Tuya control requires three things about your fireplace:

- **IP address** — assign the fireplace a static/reserved IP in your router.
- **Device ID** — a per-device identifier from Tuya.
- **Local Key** — the per-device encryption key used for local control.

### Getting the Device ID and Local Key

The simplest method uses the built-in **`tinytuya` wizard** (this integration
already depends on `tinytuya`, and you can run it from any machine with Python):

1. Make sure the fireplace is already added to the **Scandia Aurora / Smart
   Life / Tuya** app.
2. Create a free **Tuya IoT Platform** account at
   <https://iot.tuya.com>, create a **Cloud project** (Smart Home, data centre
   matching your region), and **link your app account** under
   *Devices → Link Tuya App Account*.
3. On your computer run:
   ```bash
   pip install tinytuya
   python -m tinytuya wizard
   ```
   Enter your Cloud project's **API Key**, **API Secret** and the region. The
   wizard writes a `devices.json` / `snapshot.json` containing every device's
   **`id`** (Device ID), **`key`** (Local Key) and **`ip`**.

Other tools that can extract the Local Key include the community **tuya-cloudcutter**
project and the **Tuya IoT platform → Device → Debug Device** view.

> 🔑 The Local Key **changes if you re-pair the fireplace** in the app. If the
> integration suddenly can't connect, re-run the wizard and update the key via
> **Settings → Devices & services → Scandia Fireplace → Configure**.

## Setup

When adding the integration you'll be asked for:

- **Name / model** — e.g. `Scandia Aurora 74`.
- **IP address**, **Device ID**, **Local Key**.
- **Tuya protocol version** — most Scandia units are **3.3**. If the connection
  test fails, try 3.4 or 3.5.

The integration verifies it can read the device before finishing.

## Data points (advanced)

Tuya devices expose functions as numbered **data points (DPs)**. This
integration ships with the DP mapping used by the Scandia Aurora and its
Australian siblings (Kogan, Touchstone), but firmware revisions occasionally
renumber the flame-related DPs.

If some controls are missing or behave oddly:

1. Go to **Settings → Devices & services → Scandia Fireplace →
   ⋮ → Download diagnostics**. The `raw_data_points` section lists every DP the
   device is currently reporting, with its live value.
2. Toggle functions from the fireplace panel and re-download diagnostics to see
   which DP number changes.
3. Enter the correct DP numbers under **Configure**. Leave a field blank to
   disable that feature.

### Default DP mapping

| Function | Default DP |
| --- | --- |
| Power / flame on-off | `1` |
| Heating element | `107` |
| Target temperature | `2` |
| Current temperature | `3` |
| Flame brightness | `102` |
| Flame effect / colour | `101` |
| Flame speed | `103` |
| Countdown timer | `106` |
| Child lock | `108` |

## Troubleshooting

- **`cannot_connect` when adding** — verify the IP, Device ID and Local Key,
  confirm Home Assistant is on the same subnet as the fireplace, and try a
  different protocol version. Only **one** local connection is allowed at a
  time, so fully close the Tuya app while testing.
- **Connection drops after using the app** — the Tuya app can grab the single
  local session. It should recover on the next poll; if not, reload the entry.
- **Values look wrong / controls missing** — re-map the DPs from diagnostics as
  described above.

## Disclaimer

This is an unofficial, community integration and is not affiliated with or
endorsed by Scandia or Tuya. Electric fireplaces are heating appliances —
always follow the manufacturer's safety guidance and never rely solely on
automation for an unattended appliance.

## License

Released under the [MIT License](LICENSE).
