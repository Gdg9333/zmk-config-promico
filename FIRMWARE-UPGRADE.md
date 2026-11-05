# Skree firmware upgrade review

Work branch: `zmk-firmware-upgrade-from-backup-before-zmk-upgrade`.
Baseline: `backup-before-zmk-upgrade` at `7b392a7fc1bbd8380ac3b641769b867e24fd4393`.

## Compatibility choice

Use official ZMK **v0.3.0** (`edf5c0814fd3ea202e43aad2d68fd32e882a518c`),
the newest published tag found during this investigation. It includes official
pointing support and still uses ZMK's Zephyr 3.5 branch. This keeps the change
smaller than following the moving development branch or replacing the sensor driver.

Retain `inorichi/zmk-pmw3610-driver`, pinned to
`1d9c2c68ca76012e1b1e5f6ef02fa5eadc4ca399`. Its Zephyr input events and
`zmk_keymap_*` layer calls are present in this official release. Keeping this
driver preserves its sensor initialization, CPI division, snipe, scrolling,
orientation, polling and automatic layer implementation. A driver replacement
would need a separate behavior migration and hardware validation.

Changes are limited to the official manifest remote/release, immutable driver
revision, official versioned reusable build workflow, and the supported
`CONFIG_ZMK_POINTING` option replacing deprecated `CONFIG_ZMK_MOUSE`.
The original mouse key headers remain supported by v0.3.0.

## Preserved configuration

The complete keymap, Bluetooth profile bindings, editor layout, matrix transform,
GPIO wiring, encoders, display definitions, build matrix, and central/peripheral
roles are byte-identical to the baseline. Right remains central with the sensor.
Sleep and idle configuration is unchanged, including the commented settings.
Both halves still include the `nice_view` shield. These are Nice!View SPI display
settings, not SSD1306 OLED settings; no display hardware migration is assumed.

## Existing automatic mouse layer limitation

The backup specifies `automouse-layer = <4>` but defines only layers 0 through 3.
Consequently its automatic mouse layer has no valid keymap target. This upgrade
preserves that configuration rather than inventing new mappings.

Simply adding a transparent layer 4 is insufficient: this driver's mode selection
uses only `zmk_keymap_highest_layer_active()`. A new layer 4 can mask the existing
scroll layer 2 and snipe layer 3, and ongoing movement can refresh its timeout.
A follow-up should jointly design the mouse layer and mode precedence (or migrate
to official input processors). The existing 750 ms sensor automouse timeout and
all sleep/idle settings are retained. Build success cannot establish that this
pre-existing feature works.

## Validation and review boundary

The GitHub Actions matrix builds `promicro_right nice_view`,
`promicro_left nice_view`, and `settings_reset`, all for `nice_nano_v2`.
Build results are recorded in the task report. Compilation checks API,
devicetree, Kconfig, linking and image generation; it does not test physical
sensor motion, scrolling direction, snipe transitions, displays, encoders,
Bluetooth reconnection or stored bonds. Those require a separate reviewed
hardware test. No merge or flashing is part of this change.

## Sources

- [Official v0.3.0 release notes](https://github.com/zmkfirmware/zmk/blob/v0.3.0/CHANGELOG.md)
- [Official Zephyr dependency](https://github.com/zmkfirmware/zmk/blob/v0.3.0/app/west.yml)
- [Official pointing options and compatibility alias](https://github.com/zmkfirmware/zmk/blob/v0.3.0/app/src/pointing/Kconfig)
- [PMW3610 driver and mode selection](https://github.com/inorichi/zmk-pmw3610-driver/blob/1d9c2c68ca76012e1b1e5f6ef02fa5eadc4ca399/src/pmw3610.c)
