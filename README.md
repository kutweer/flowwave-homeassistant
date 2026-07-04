# Flowwave for Home Assistant

Send your Home Assistant energy sensors to **[Flowwave](https://flowwave.nl)** — your home‑energy control tower — with a few clicks. No `rest_command`, no `automations.yaml`, no YAML at all.

[![hacs](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

## Why

Flowwave turns your meter data into live power flow, day‑ahead price windows, solar insights and comparisons. If you already have a P1 reader, an inverter integration or any energy sensors in Home Assistant, this integration streams them to your Flowwave account every few seconds. Power sensors are auto‑converted to watts from their own unit, so a **kW** inverter sensor and a **W** meter sensor both just work.

Prefer plug‑and‑play hardware instead? The open‑source **[Flow One](https://flowwave.nl/setup)** P1 dongle does the same without Home Assistant.

## Install

### Via HACS (recommended)
1. HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/kutweer/flowwave-homeassistant`, category **Integration**.
3. Search **Flowwave**, install, and restart Home Assistant.

### Manually
Copy `custom_components/flowwave` into your Home Assistant `config/custom_components/` folder and restart.

## Set up
1. In Flowwave: **flowwave.nl → Devices → Connect Flow One**, and copy the **device token**.
2. In Home Assistant: **Settings → Devices & services → Add integration → Flowwave**.
3. Paste the token, pick your sensors:
   - **Electricity used right now** (required)
   - Electricity returned to the grid *(if you have solar)*
   - Solar production *(from your inverter, if available)*
   - Gas meter total, Voltage *(optional)*
4. Done. Your data appears on your Flowwave dashboard within ~30 seconds.

Change your sensors any time via the integration's **Configure** button — no need to remove and re‑add it.

## What gets sent
Only the sensors you choose, as numeric readings, to `https://flowwave.nl/api/ingest`, authenticated with your device token. Nothing else leaves Home Assistant. The token can be revoked from your Flowwave Devices page at any time.

## License
MIT — see [LICENSE](LICENSE).
