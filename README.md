# Scandia Fireplace — Home Assistant integration

A [HACS](https://hacs.xyz/) custom integration for **Scandia Aurora electric
fireplaces** (36" / 50" / **74"**). The Scandia Aurora fires are Tuya-based
devices normally controlled from the **Scandia Aurora Wi-Fi** app (a re-branded
Tuya / Smart Life app). This integration brings them into Home Assistant with a
**simple sign-in** — no Tuya developer account, no keys to copy — and lets you
choose **cloud** or **local** control.

You sign in exactly like Home Assistant's official Tuya integration: enter a
short **user code** from the Smart Life app and scan a **QR code**. That single
sign-in retrieves both the cloud token *and* the device's local key + IP, so you
can pick how it's controlled:

- **☁️ Cloud** — commands go through Tuya's cloud. Works from anywhere, no local
  network setup.
- **🏠 Local** — commands go **directly over your LAN** (via `tinytuya`) using
  the key retrieved during sign-in. Faster, and keeps working with no internet.

Either way you get proper, fireplace-specific entities — a button for every
flame colour, a heater and timer dropdown, and a power switch — rather than the
generic controls the official Tuya integration produces.

> 🔁 **Not a Scandia?** The Aurora is a widely rebadged Tuya OEM fireplace. See
> **[Supported fireplaces](#supported-fireplaces)** — Benrocks, Yacoiel,
> Velaychimney, Auchsiag, Mystflame and many unbranded inserts use the same
> board and work via a selectable device profile (or the address remap).

> 📖 **Full step-by-step instructions for both modes:** see
> **[docs/SETUP.md](docs/SETUP.md)**. The sections below are a condensed
> overview.

## Features

| Entity | Platform | What it controls |
| --- | --- | --- |
| Power | `switch` | Turn the whole fireplace on/off |
| Flame colour | `button` (×13) | One button per flame colour — tap to apply |
| Flame log colour | `button` (×13) | One button per fuel-bed / ember colour |
| Top light | `button` (×4) | Downlight: Off / Yellow / Blue / Purple (Aurora) |
| Heater | `select` | Off / Low (750W) / High (1500W) |
| Timer | `select` | Countdown auto-off (Off / 1h–6h) |
| Flame / log / top-light colour | `sensor` | The currently selected colour (feedback for the buttons) |
| Endpoint _n_ | `sensor` (diagnostic) | Auto-discovered raw data points, disabled by default |

Controls are created only for the functions your profile maps, so you won't see
buttons your unit doesn't support. This unit has no dimmer or thermostat, so
there is no brightness slider or temperature — the flame is entirely preset
(colour) based.

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

1. **User code** — in the Smart Life app: **Me → ⚙ Settings → Account and
   Security → User Code**. Enter it in Home Assistant.
2. **Scan the QR code** — in the app tap **＋ (top right) → Scan**, scan the code
   Home Assistant shows, then press **Submit**.
3. **Select your fireplace** from the account's device list.
4. **Choose Cloud or Local:**
   - **Cloud** finishes immediately.
   - **Local** confirms the fireplace's IP (auto-detected from the LAN where
     possible — otherwise enter it from your router and reserve it) and protocol
     version, then verifies it can reach the device.

> You need a second screen to display the QR code (Home Assistant on a computer)
> while you scan it with the phone running the Smart Life app.

### Which mode should I pick?

- **Local** is best if Home Assistant is on the same network as the fireplace:
  it's faster and doesn't depend on the internet. If the local key ever changes
  (e.g. after re-pairing), the integration re-fetches it from the cloud
  automatically.
- **Cloud** is the safe default if the fireplace is on a different network/VLAN,
  or local control won't connect.

Local mode is only offered if the sign-in returned a local key for your device.

## Function mapping (advanced)

Tuya devices address functions differently in each mode: **function codes**
(cloud, e.g. `switch`, `countdown_set`) or **numbered data points** (local, e.g.
`1`, `101`). In local mode the defaults come from the **device profile** you
picked at setup. If a control is missing or wrong:

1. **Settings → Devices & services → Scandia Fireplace → ⋮ → Download
   diagnostics**. The `raw_status` section lists every address the device
   reports with its live value, `address_map` shows the current mapping, and
   `endpoint_spec` includes the full Tuya function spec from the cloud.
2. Toggle a function on the fireplace/app and re-download (or enable the
   auto-discovered **Endpoint _n_** diagnostic sensors) to see which address
   changes.
3. Enter the correct addresses under **Configure**. Leave a field blank to
   disable that feature.

### Default mapping (local DPs)

| Function | Aurora profile | Auchsiag profile |
| --- | --- | --- |
| Power | `1` | `1` |
| Heater (Off/Lo/Hi) | `4` | `5` |
| Top light colour | `5` | _none_ |
| Countdown timer | `19` | `13` |
| Flame colour | `101` (`L01`–`L13`) | `17` (named) |
| Flame log / ember colour | `102` (`C01`–`C13`) | `101` (named) |

In cloud mode the Tuya API only exposes `switch` (power) and `countdown_set`
(timer) for this OEM, so the colour/heater controls are available in **local
mode only**.

## Supported fireplaces

This is a rebadged Tuya OEM fireplace sold under many names. Pick the profile
that matches your unit at setup (local mode). Where the data points differ, use
the **Configure** address remap.

| Profile | Known brands / models | Notes |
| --- | --- | --- |
| **Aurora** | Scandia Aurora (36″/50″/74″); most "**13 flame / 13 fuel-bed / 3 top-light**" inserts — Benrocks, Yacoiel, Velaychimney, Mystflame, many unbranded Amazon inserts (33″–88″) | Numbered colours, top light |
| **Auchsiag** | Auchsiag and named-colour clones (Auto/Red/Yellow/… flame, named embers) | No top light; flame speed/brightness show as diagnostic endpoints |

Confidence varies by brand and rebadges sometimes ship different data points —
if a colour button does nothing, download diagnostics and remap. PRs adding new
brand profiles are welcome.

## Troubleshooting

- **`login_error`** — re-check the user code (it changes if you log out of the
  app) and make sure you scanned the QR with the **Smart Life / Tuya** app
  before pressing Submit. The QR expires after a few minutes; if it does, start
  again.
- **Local mode not offered** — the cloud didn't return a local key for this
  device; use Cloud mode.
- **`cannot_connect` (local)** — verify the IP, confirm Home Assistant is on the
  same subnet, try a different protocol version, and fully close the Tuya app
  while testing (only one local session is allowed at a time).
- **Re-authentication needed** — the cloud session expired; follow the prompt to
  scan a fresh QR code. Your mode and settings are kept.
- **Values look wrong / controls missing** — re-map the addresses from
  diagnostics as described above.

## Disclaimer

This is an unofficial, community integration and is not affiliated with or
endorsed by Scandia or Tuya. Electric fireplaces are heating appliances —
always follow the manufacturer's safety guidance and never rely solely on
automation for an unattended appliance.

## License

Released under the [MIT License](LICENSE).
