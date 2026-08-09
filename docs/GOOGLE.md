# "Hey Google, it's game day"

How to make a spoken phrase set the fireplace to a fixed scene — power on, flame
colour 4, flame log colour 4.

## How the pieces fit together

Three separate things are involved, and it's easy to confuse them:

| Piece | Direction | What it does here |
| --- | --- | --- |
| **Google Cast** integration in HA | HA → speaker | Lets Home Assistant cast media and TTS *to* your Google Home Mini. **Not used for this.** |
| **`google_assistant`** integration in HA | Google → HA | Lets Google see and control Home Assistant entities. **This is the one that matters.** |
| **Routine** in the Google Home app | phrase → action | Maps the words "it's game day" onto the action. |

Having your Google Home Mini listed in Home Assistant (via Google Cast) does
**not** mean Google can talk to Home Assistant. The Mini is only the microphone
that hears the phrase; the command travels Google → `google_assistant` → HA.

## Step 1 — Create the script

Add to `configuration.yaml` (or your `scripts.yaml`, dropping the leading
`script:` key if so):

```yaml
script:
  game_day:
    alias: Game Day
    icon: mdi:football
    mode: single
    sequence:
      - action: scandia_fireplace.set_state
        target:
          entity_id: switch.scandia_fireplace   # your fireplace's power switch
        data:
          power: true
          flame_colour: "Colour 4"
          flame_log_colour: "Colour 4"
```

Replace `switch.scandia_fireplace` with your actual power-switch entity ID
(**Settings → Devices & services → Scandia Fireplace → the device**; the power
switch is the one named after the device itself).

`scandia_fireplace.set_state` sends all three settings to the fireplace in a
single write, so the scene lands at once instead of visibly stepping through
colours. When the fireplace is currently off it switches on first, waits a
second for the board to wake, then sends the colours — a board that has just
powered up can otherwise drop colour values.

### Optional: spoken confirmation

This is where the **Google Cast** side does become useful. Because your Google
Home Mini is in Home Assistant as a media player, the script can talk back
through it:

```yaml
      - action: tts.speak
        target:
          entity_id: tts.google_translate_en_com   # your TTS entity
        data:
          media_player_entity_id: media_player.tv_room_speaker
          message: "Game day. Fireplace is on."
```

Append that to the end of the `sequence:`. Adjust the `tts.` entity to whichever
TTS engine you have configured (**Settings → Devices & services → Entities**,
filter by `tts.`).

> **Local mode only.** Flame and flame-log colours aren't exposed by the Tuya
> cloud for this OEM, so this script needs your entry to be in local mode. It
> is, so you're fine — but if you ever switch to cloud, the colour settings will
> be skipped with a warning in the log.

Reload with **Developer tools → YAML → Reload scripts**, then test it from
**Developer tools → Actions → `script.game_day` → Perform action** before
involving Google at all. Get this working first; everything after it is just
plumbing.

## Step 2 — Expose the script to Google

Scripts show up to Google Assistant as **scenes**. In your existing
`google_assistant:` block:

```yaml
google_assistant:
  project_id: your-actions-project-id
  service_account: !include SERVICE_ACCOUNT.JSON
  report_state: true
  exposed_domains:
    - script          # add this if you already have an exposed_domains list
  entity_config:
    script.game_day:
      name: Game Day
      expose: true
```

Notes:

- If you already have an `exposed_domains:` list, `script` must be added to it —
  otherwise the script won't be published no matter what `entity_config` says.
- If you have no `exposed_domains:` at all, everything is exposed by default and
  `entity_config` alone is enough.
- The fireplace's own entities do **not** need to be exposed for this to work.
  Only the script does.

Restart Home Assistant after editing.

## Step 3 — Sync the new device to Google

Say to any of your speakers:

> "Hey Google, sync my devices."

Then check the Google Home app — **Game Day** should appear as a scene. If it
doesn't, nothing further will work; see Troubleshooting below.

## Step 4 — Create the Routine

In the **Google Home** app:

1. **Automations** (or **Routines**) → **＋ Add**.
2. **Starter** → **When I say a phrase** → type `it's game day`.
   Add a couple of variants while you're there so it's forgiving:
   `it is game day`, `game day`.
3. **Action** → **Adjust home devices** → find **Game Day** → set it to
   **Activate**.
   If it isn't listed, use **Try adding your own** and type: `Activate Game Day`.
4. Save.

Now: **"Hey Google, it's game day."**

## Troubleshooting

- **"Game Day" never appears in the Google Home app** — the `google_assistant`
  link isn't working. Confirm it's actually configured (search
  `configuration.yaml` for `google_assistant:`) and that account linking was
  completed in the Google Home app. Having the Mini in HA via Google Cast is
  not the same thing and is not sufficient.
- **Google says "Sorry, I don't understand"** — the Routine's starter phrase
  didn't match. Phrases are matched fairly literally; add variants.
- **Google says it worked but nothing happens** — test `script.game_day`
  directly in Developer tools. If the script fails there, the problem is in
  Home Assistant, not Google.
- **The fireplace turns on but the colours don't change** — check the Home
  Assistant log for a warning from `scandia_fireplace`. Either the colour
  functions aren't mapped for your profile (**Configure** → address remap), or
  the entry is in cloud mode.
- **`'Colour 4' is not a valid value`** — the error message lists every value
  your profile accepts; use one of those. The raw device values (`L04`, `C04`)
  work too.

## Without the custom service

If you'd rather not depend on `scandia_fireplace.set_state`, the same scene works
with the plain entities — three writes instead of one, so it steps through
visibly:

```yaml
script:
  game_day:
    alias: Game Day
    sequence:
      - action: switch.turn_on
        target:
          entity_id: switch.scandia_fireplace
      - delay: "00:00:01"
      - action: button.press
        target:
          entity_id:
            - button.scandia_fireplace_flame_colour_4
            - button.scandia_fireplace_flame_log_colour_4
```

Check the exact button entity IDs on the device page — they're derived from the
device name, so yours will differ.
