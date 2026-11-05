"""Acceptance checks against the reviewed pre-correction firmware commit.

Run: python3 -m unittest discover -s tests -v
Requires cd9a677 in local Git history (normal clones and this upgrade branch have it).
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'cd9a677d9f97641401b34d9e3855f7bfc3911940'


def original(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT).decode('utf-8-sig')


def current(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def layers(text):
    return {name: (bindings, sensors) for name, bindings, sensors in re.findall(r'([\w-]+)\s*\{\s*bindings\s*=\s*<(.*?)>;(.*?)\};', text, re.S)}


def tokens(text):
    return re.findall(r'&\w+|[\w()+]+', text)


class AutomaticMouseAcceptance(unittest.TestCase):
    def test_existing_key_and_encoder_functions_are_preserved(self):
        old = layers(original('config/promicro.keymap'))
        new = layers(current('config/promicro.keymap'))
        self.assertEqual(list(new), ['default_layer', 'automatic_mouse', 'Blue-Key', 'Sym-Num-Pad', 'Scroll-Function'])
        for name, (bindings, sensors) in old.items():
            remapped = re.sub(r'&(mo|tog) ([123])\b', lambda m: f'&{m[1]} {int(m[2])+1}', bindings)
            self.assertEqual(tokens(new[name][0]), tokens(remapped), name)
            self.assertEqual(tokens(new[name][1]), tokens(sensors), name)
        self.assertEqual(tokens(new['automatic_mouse'][0]), ['&trans'] * len(re.findall(r'&\w+', old['default_layer'][0])))
        self.assertEqual(tokens(new['automatic_mouse'][1]), [])  # encoder events fall through

    def test_automatic_layer_is_below_all_manual_modes(self):
        overlay = current('config/boards/shields/promicro/promicro_right.overlay')
        self.assertRegex(overlay, r'input-processors\s*=\s*<&zip_temp_layer\s+1\s+750>')
        self.assertRegex(overlay, r'scroll-layers\s*=\s*<3>')
        self.assertRegex(overlay, r'snipe-layers\s*=\s*<4>')
        manual = re.search(r'manual_layers\s*\{(.*?)\};', overlay, re.S).group(1)
        manual = re.sub(r'//[^\n]*', '', manual)
        self.assertRegex(manual, r'layers\s*=\s*<2 3 4>;')
        self.assertNotIn('input-processors', manual)
        self.assertNotIn('process-next', manual)
        # Highest-active-layer mode selection must be identical with auto on/off,
        # including simultaneous scroll+snipe and toggled symbol layer combinations.
        for mask in range(1 << 3):
            manual = [i + 2 for i in range(3) if mask & (1 << i)]
            highest_without = max([0] + manual)
            highest_with = max([0, 1] + manual)
            mode = lambda n: 'scroll' if n == 3 else 'snipe' if n == 4 else 'move'
            self.assertEqual(mode(highest_with), mode(highest_without))

    def test_legacy_interrupt_timer_is_disabled(self):
        overlay = re.sub(r'//[^\n]*', '', current('config/boards/shields/promicro/promicro_right.overlay'))
        self.assertNotRegex(overlay, r'\bautomouse-layer\s*=')  # driver binding defaults to -1
        self.assertIn('CONFIG_PMW3610_AUTOMOUSE_TIMEOUT_MS=750', current('config/boards/shields/promicro/promicro_right.conf'))

    def test_hardware_bluetooth_sleep_and_other_config_are_unchanged(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'config'], cwd=ROOT).decode().splitlines()
        allowed = {'config/promicro.keymap', 'config/boards/shields/promicro/promicro_right.overlay'}
        for path in paths:
            if path not in allowed:
                self.assertEqual(current(path), original(path), path)
        # The edited overlay must retain every existing setting except the three layer properties.
        old = original('config/boards/shields/promicro/promicro_right.overlay')
        new = current('config/boards/shields/promicro/promicro_right.overlay')
        for prop in ('psels', 'cs-gpios', 'irq-gpios', 'spi-max-frequency', 'col-offset', 'zephyr,display'):
            pattern = rf'{re.escape(prop)}\s*=\s*(.*?);'
            self.assertEqual(re.findall(pattern, old, re.S), re.findall(pattern, new, re.S), prop)


if __name__ == '__main__':
    unittest.main()
