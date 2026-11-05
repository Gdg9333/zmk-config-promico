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

The original four layers retain their physical key and encoder functions. A new,
fully transparent automatic mouse layer is inserted at index 1, below every
manual layer. Existing layer targets and the sensor's mode layer indices are
shifted together; Bluetooth profile numbers are NOT changed:

| Layer | Before | After |
| --- | --- | --- |
| Base | 0 | 0 |
| Automatic mouse | undefined 4 | 1 |
| Blue-Key | 1 | 2 |
| Sym-Num-Pad / trackball scrolling | 2 | 3 |
| Scroll-Function / trackball snipe | 3 | 4 |

All Bluetooth, sleep/idle, GPIO wiring, matrix transform, encoder hardware,
display and sensor tuning settings remain unchanged. Right remains central.
Both halves still include the `nice_view` shield (Nice!View SPI displays, not
SSD1306 OLED displays). The editor JSON describes physical hardware/layout and
is unchanged. Numeric manual layer indices and displayed layer numbers change;
physical key functions and Bluetooth profile indices do not.

## Automatic mouse layer correction

The reviewed upgrade at `cd9a677` retained the backup's invalid
`automouse-layer = <4>` with only four layers. Both old and official ZMK reject
that activation with `-EINVAL`, which the driver ignores. This was not a
trackball movement disable, but automatic layer switching could not work.

The correction uses official ZMK v0.3.0's `zip_temp_layer` input processor on
the PMW3610 listener. Real movement events in base/automatic mode activate the
transparent layer 1 and refresh its **750 ms** timeout. The official processor
expires it through work queues, in thread context. Bluetooth, scrolling and
snipe layers bypass the processor, preserving their motion processing and
preventing those events from refreshing the automatic layer. An already-active
automatic layer can expire underneath a manual layer without changing its keys
or trackball mode. Processing continues to the normal HID listener.

Omitting the driver's optional `automouse-layer` property selects its binding
default of -1, compiling out the legacy automatic-layer timer. This avoids layer
notifications from its interrupt-context timer, which would reach mutex-taking
display listeners. There are **no PMW3610 driver source changes**, replacements,
or CPI/scroll/snipe algorithm changes. The existing driver Kconfig timeout is
retained at 750, but the active timeout is now the listener's 750 ms parameter.

Layer 1 inherits all key and encoder bindings. There are no new mouse shortcuts,
click mappings, scrolling triggers or precision mappings: with this keymap the
practical benefit is correct, safe automatic layer state (and possible display
feedback), not faster pointer operation or improved Bluetooth connectivity.
Future bindings on this layer would be a separate mapping change.

Risks to test physically include layer-number/UI expectations, timing on rapid
motion/manual-layer transitions, motion during held keys, and encoder fallthrough.
The official processor schedules changes asynchronously; 750 ms is the configured
idle timeout, not a hard real-time deadline under CPU load. No key-press
cancellation or typing suppression is newly configured.

Regression checks: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`.
They compare mappings and unrelated settings with `cd9a677` in Git history and
check mode precedence for every manual-layer combination with auto on/off.

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
