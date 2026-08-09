# Scandia Fireplace — Full Setup Guide

Complete instructions for installing and configuring the integration in **both**
connection modes:

- [☁️ Cloud mode](#cloud-mode) — control through Tuya's cloud (works anywhere).
- [🏠 Local mode](#local-mode) — control directly over your home network (faster,
  no internet dependency).

Both modes use the **same one-time sign-in** — a user code from the Smart Life
app plus a QR scan. There is no Tuya developer account and nothing to copy by
hand.

---

## Contents

1. [Before you start](#1-before-you-start)
2. [Install the integration (HACS)](#2-install-the-integration-hacs)
3. [Sign in (both modes)](#3-sign-in-both-modes)
4. [Cloud mode](#cloud-mode)
5. [Local mode](#local-mode)
6. [After setup: check your entities](#6-after-setup-check-your-entities)
7. [Fixing missing or wrong controls](#7-fixing-missing-or-wrong-controls)
8. [Switching modes](#8-switching-modes)
9. [Re-authentication](#9-re-authentication)
10. [Troubleshooting](#10-troubleshooting)
11. [FAQ](#11-faq)

---

## 1. Before you start

You need:

- **The fireplace already added to the Smart Life (or Tuya Smart) app** and
  working there. If it isn't, pair it in the app first — power the fireplace,
  open the app, tap **＋ → Add Device**, and follow the prompts.
- **Home Assistant with HACS installed.** (HACS install guide:
  <https://hacs.xyz/docs/setup/download>.)
- **A second screen** for sign-in — you'll view a QR code in Home Assistant (on
  a computer/tablet) and scan it with the phone running the Smart Life app.
- For **local mode only:** Home Assistant must be on the **same network** as the
  fireplace, and ideally you can set a **reserved/static IP** for the fireplace
  in your router.

---

## 2. Install the integration (HACS)

1. In Home Assistant, go to **HACS → Integrations**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Paste the repository URL and choose category **Integration**:
   ```
   https://github.com/HallyAus/Scandia
   ```
   Click **Add**.
4. Search HACS for **Scandia Fireplace**, open it, and click **Download**.
5. **Restart Home Assistant** (Settings → System → ⋮ → Restart).

> **Manual alternative:** copy the `custom_components/scandia_fireplace` folder
> into your Home Assistant `config/custom_components/` directory and restart.

---

## 3. Sign in (both modes)

This part is identical whether you end up choosing cloud or local.

1. Go to **Settings → Devices & services → Add integration**, search for
   **Scandia Fireplace**, and click it.

2. **Get your user code.** On your phone, open the **Smart Life** (or Tuya Smart)
   app:
   - Tap **Me** (bottom right).
   - Tap the **⚙ gear / Settings** icon (top right).
   - Tap **Account and Security**.
   - Read the **User Code** near the bottom. It's a short code of letters/digits.

3. Type that **User Code** into Home Assistant and submit.

4. Home Assistant shows a **QR code**. In the Smart Life app:
   - Tap the **＋** (top right) → **Scan**.
   - Scan the QR code on your Home Assistant screen.
   - Back in Home Assistant, press **Submit**.

   > The QR code expires after a few minutes. If it times out, cancel and start
   > the sign-in again.

5. **Select your fireplace** from the list of devices on your account.

6. **Choose a mode** — Cloud or Local. Continue with the matching section below.

---

## Cloud mode

**Best if:** the fireplace is on a different network/VLAN from Home Assistant,
local control won't connect, or you simply want the simplest setup.

**How it behaves:** commands and status updates go through Tuya's cloud. Requires
an internet connection. Updates are usually near-instant (Tuya pushes changes),
with periodic polling as a backup.

### Steps

1. Complete [Sign in](#3-sign-in-both-modes).
2. On the mode screen, choose **Cloud (via Tuya)**.
3. That's it — the fireplace is added immediately.

There's nothing else to configure for cloud mode. Skip to
[After setup](#6-after-setup-check-your-entities).

---

## Local mode

**Best if:** Home Assistant is on the **same network** as the fireplace. Control
is faster and keeps working even if your internet is down.

**How it behaves:** commands go **directly to the fireplace over your LAN**. The
**local key** needed for this is retrieved automatically during sign-in — you
never extract it by hand. If the key ever changes (for example after re-pairing
the fireplace in the app), the integration detects the failure and re-fetches
the new key from the cloud automatically.

> Local mode only appears if the sign-in returned a local key for your device.
> If you get a "local key not available" message, use Cloud mode instead.

### Steps

1. Complete [Sign in](#3-sign-in-both-modes).
2. On the mode screen, choose **Local (direct over your network)**.
3. Home Assistant shows a **Confirm local connection** form:
   - **IP address** — this is **auto-detected** where possible (Home Assistant
     listens for the fireplace's broadcast on your LAN, and also uses the IP the
     cloud reported). If the field is filled in, just check it looks right. If
     it's blank, enter the fireplace's IP manually — find it in your router's
     device/DHCP list (look for the Tuya/fireplace device).
   - **Tuya protocol version** — pre-filled (usually **3.3**). Leave it unless
     the connection test fails, then try 3.4 or 3.5.
4. Submit. Home Assistant verifies it can reach the fireplace before finishing.

### Reserve the IP address (recommended)

Local control talks to the fireplace by IP. If your router later hands it a
different address, control stops until it's updated. To prevent that, set a
**DHCP reservation** (a.k.a. static lease) for the fireplace in your router so it
always gets the same IP. The exact steps vary by router — look for
**DHCP reservations** / **Address reservation** / **Static leases** and bind the
fireplace's MAC address to a fixed IP.

> Tip: only one device can hold the fireplace's single local connection at a
> time. If local setup won't connect, fully close the Smart Life app and try
> again.

---

## 6. After setup: check your entities

Open **Settings → Devices & services → Scandia Fireplace → the device**. You
should see some or all of:

| Entity | What it is |
| --- | --- |
| **Fireplace** (climate) | Power, heat vs. flame-only mode, target & current temperature, presets |
| **Flame** (light) | Flame on/off, brightness, colour effect |
| **Flame speed** (select) | Animation speed |
| **Auto-off timer** (number) | Countdown timer in hours |
| **Child lock** (switch) | Child lock |
| **Current temperature** (sensor) | Room temperature |
| **Power / Energy** (sensor) | Live watts / cumulative kWh (if your unit reports them) |

Only functions your fireplace actually exposes appear. If something you expected
is missing or behaves oddly, see the next section.

---

## 7. Fixing missing or wrong controls

Tuya devices address their functions differently in each mode:

- **Cloud mode** uses **function codes** — words like `switch`, `temp_set`,
  `bright_value`.
- **Local mode** uses **data point (DP) numbers** — like `1`, `2`, `102`.

The integration ships with sensible defaults, but a few functions (heating
element, flame effect/speed, presets, power/energy sensors) vary between models.
Here's how to find and set the right ones:

1. Go to **Settings → Devices & services → Scandia Fireplace → ⋮ → Download
   diagnostics**. Open the downloaded file and find:
   - **`raw_status`** — every address the device is currently reporting, with
     its live value.
   - **`address_map`** — the mapping the integration is currently using.
2. Change one function on the fireplace or in the Smart Life app (e.g. turn the
   flame colour to blue), then download diagnostics again and see **which
   address changed**. That's the address for that function.
3. In Home Assistant, open **Scandia Fireplace → ⋮ → Configure**. Enter the
   correct address for each function (a **code** in cloud mode, a **DP number**
   in local mode). **Leave a field blank to disable** that feature.
4. Save — the integration reloads with the new mapping.

### Default mapping reference

| Function | Cloud code | Local DP |
| --- | --- | --- |
| Power / flame on-off | `switch` | `1` |
| Target temperature | `temp_set` | `2` |
| Current temperature | `temp_current` | `3` |
| Flame brightness | `bright_value` | `102` |
| Flame effect / colour | _unset_ | `101` |
| Flame speed | _unset_ | `103` |
| Countdown timer | `countdown_set` | `106` |
| Child lock | `child_lock` | `108` |
| Heat preset | `mode` | _unset_ |
| Heating element | _unset_ | `107` |
| Power sensor (W) | _unset_ | _unset_ |
| Energy sensor (kWh) | _unset_ | _unset_ |

---

## 8. Switching modes

The mode (cloud or local) is chosen during setup and stored with the entry. To
switch:

1. **Settings → Devices & services → Scandia Fireplace → ⋮ → Delete**.
2. Add the integration again and choose the other mode.

Your Smart Life sign-in is remembered on your account, so re-adding is quick.

---

## 9. Re-authentication

Cloud sessions can expire. If Home Assistant shows a **"re-authentication
required"** notification for Scandia Fireplace:

1. Click it (or **Settings → Devices & services → Scandia Fireplace →
   Reconfigure**).
2. Enter your user code and scan a fresh QR code, exactly as in
   [Sign in](#3-sign-in-both-modes).

Your mode and all settings are preserved. This applies to local mode too,
because local mode uses the cloud session to refresh the local key.

---

## 10. Troubleshooting

| Symptom | Fix |
| --- | --- |
| **`login_error` during sign-in** | Re-check the user code (it changes if you log out of the app). Make sure you scanned the QR with the **Smart Life/Tuya** app, not a generic camera, before pressing Submit. If the QR expired, start again. |
| **"No devices found"** | Confirm the fireplace appears in the Smart Life app under the same account whose user code you used. |
| **Local mode not offered** | The cloud didn't return a local key for this device — use Cloud mode. |
| **`cannot_connect` (local)** | Check the IP, confirm Home Assistant is on the same subnet, try protocol version 3.4/3.5, and fully close the Smart Life app while testing. |
| **Local worked, then stopped** | The fireplace's IP probably changed — reserve it in your router (see [Reserve the IP](#reserve-the-ip-address-recommended)), then delete and re-add, or wait for the automatic key refresh. |
| **Re-authentication required** | Follow [section 9](#9-re-authentication). |
| **A control is missing or does the wrong thing** | Re-map its address from diagnostics — see [section 7](#7-fixing-missing-or-wrong-controls). |

Still stuck? Open an issue at
<https://github.com/HallyAus/Scandia/issues> and attach the (redacted)
diagnostics download.

---

## 11. FAQ

**Do I need a Tuya developer / IoT account?**
No. The user-code + QR sign-in is all that's required for either mode.

**Is cloud or local better?**
Local is faster and works without internet, but needs Home Assistant on the same
network as the fireplace. Cloud is more forgiving of network setups. You can
switch anytime by re-adding the integration.

**Does local mode still need the internet?**
Only occasionally — to refresh the cloud session/local key if it changes.
Day-to-day control is fully local.

**Is my Tuya password shared with Home Assistant?**
No. You never enter your password; the QR scan authorises the session on your
account.

**The local key — do I have to find it myself?**
No. It's retrieved automatically during sign-in, and refreshed automatically if
it changes.
