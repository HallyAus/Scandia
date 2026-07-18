# Scandia Fireplace — Home Assistant integration

A [HACS](https://hacs.xyz/) custom integration that brings **Scandia Aurora
electric fireplaces** (36" / 50" / **74"**) into Home Assistant **without the
cloud**. It talks to the fireplace directly over your LAN using the local Tuya
protocol, so control stays fast and keeps working even if the internet — or
Tuya's servers — are down.

The Scandia Aurora fires are Tuya-based devices that you normally control from
the **Scandia Aurora Wi-Fi** app (a re-branded Tuya/Smart Life app). This
integration replaces that app for day-to-day control inside Home Assistant.

> ℹ️ Setup is **cloud-assisted but runs locally**: you enter your Tuya IoT
> credentials once, the integration pulls the fireplace's **Local Key**
> automatically from the Tuya cloud, and from then on all control happens over
> your LAN. It even re-fetches the key from the cloud automatically if it
> changes (e.g. after re-pairing), so the connection self-heals.

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

You need a **Tuya IoT Platform project** (free) linked to your Scandia Aurora /
Smart Life / Tuya app account. This is what lets the integration read your
fireplace's local key from the cloud. You do **not** run any wizard or copy the
local key by hand — the integration does that for you.

### One-time Tuya IoT project setup

1. Make sure the fireplace is already added to the **Scandia Aurora / Smart
   Life / Tuya** app and working there.
2. Create a free account at the **Tuya IoT Platform**
   (<https://iot.tuya.com>).
3. Create a **Cloud project**:
   - Development method: **Smart Home**
   - Data centre: the region closest to you (for Australia, usually
     **Western America** → region `us`, sometimes **Central Europe** → `eu`).
   - After creation, note the project's **Access ID / Client ID** and
     **Access Secret / Client Secret**.
4. Under the project's **Devices → Link Tuya App Account**, scan the QR code
   with your Scandia/Smart Life app (**Me → ⚙ → scan**) to link your account.
   Your fireplace now appears under the project's linked devices.
5. Grab any one **Device ID** from the app (**device → ✏ / Device Information →
   Virtual ID**) — the integration only needs it to look up your project; you'll
   pick the actual fireplace from a list during setup.

> 🔑 You never handle the local key. If it ever changes (re-pairing the
> fireplace resets it), the integration detects the failed connection and pulls
> the new key from the cloud automatically.

## Setup

When adding the integration you'll go through two quick steps:

**Step 1 — Tuya cloud credentials**
- **Region** — your project's data centre (try `us` first for Australia).
- **Access ID / Client ID** and **Access Secret / Client Secret** — from your
  IoT project.
- **Sample Device ID** — any device from your account.

The integration then lists every device on the account.

**Step 2 — Select your fireplace**
- **Fireplace** — pick it from the dropdown. Its local key and protocol version
  are filled in automatically.
- **IP address** — **auto-detected**. On opening this step the integration
  listens for the Tuya UDP broadcasts your fireplace sends on the LAN and
  matches them to its device ID, pre-filling the IP. If your network blocks
  those broadcasts (some VLAN/Docker setups do), the field is left blank —
  enter the IP from your router's device list. Either way, reserve the IP so it
  won't change.
- **Tuya protocol version** — pre-filled from the cloud; most Scandia units are
  **3.3**. If the local test fails, try 3.4 or 3.5.

The integration verifies it can reach the fireplace locally before finishing.

> 💡 Auto-detection needs Home Assistant to be on the **same subnet** as the
> fireplace and able to receive UDP broadcasts (ports 6666/6667/7000). Host-mode
> and standard add-on installs get this automatically; heavily segmented
> networks may need the IP entered by hand.

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

- **`cloud_error` / no devices** — check the region, Access ID and Access
  Secret, and that your IoT project uses the **Smart Home** data source with
  your app account linked. Newly created projects can take a few minutes before
  the API returns devices.
- **`cannot_connect` when selecting the device** — verify the IP, confirm Home
  Assistant is on the same subnet as the fireplace, and try a different protocol
  version. Only **one** local connection is allowed at a time, so fully close
  the Tuya app while testing.
- **Connection drops after using the app** — the Tuya app can grab the single
  local session. It should recover on the next poll; if not, reload the entry.
- **Fireplace got a new IP** — open the integration entry → **⋮ → Reconfigure**
  to update the IP (it's re-detected from the LAN automatically). Reserving the
  IP in your router avoids this entirely.
- **Values look wrong / controls missing** — re-map the DPs from diagnostics as
  described above.

## Disclaimer

This is an unofficial, community integration and is not affiliated with or
endorsed by Scandia or Tuya. Electric fireplaces are heating appliances —
always follow the manufacturer's safety guidance and never rely solely on
automation for an unattended appliance.

## License

Released under the [MIT License](LICENSE).
