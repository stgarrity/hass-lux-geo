# hass-lux-geo
HACS-compatible Home Assistant integration for Lux Geo thermostats

This is a custom component for Home Assistant to support the Lux Geo Thermostat.

I have only tested (ish) with a single device that controls a millivolt propane heater
(hence why I needed to use the Lux Geo, as well as why this only supports heat mode so far).

## Limitations

- Only supports one device currently (the first device at the first location)
- Only supports heat (not cool) mode

## Potential improvements

- [ ] Add an icon :)
- [ ] Switch always_update to false for better performance?
- [ ] Handle token expiration better
- [ ] Switch `integration_type` from `device` to `hub` to support multiple devices? Or can multiple config entries support this automatically?
