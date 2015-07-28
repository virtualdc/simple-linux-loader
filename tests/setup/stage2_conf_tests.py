import unittest
import StringIO
import stage2


class TestStage2Builder(unittest.TestCase):

    def setUp(self):
        f = StringIO.StringIO("\x00" * 512)
        self.stage2 = stage2.Stage2(f)

    def test_long_cmd(self):
        with self.assertRaises(stage2.Stage2Error):
            self.stage2.set_command_line("\x01" * stage2.max_command_line_size)

    def test_get_set(self):
        self.stage2.set_kernel_blocklist_lba(0x0123456789ABCDEF)
        self.stage2.set_initrd_blocklist_lba(0x0011223344556677)
        self.stage2.set_kernel_size(0x8899AABB)
        self.stage2.set_initrd_size(0xCCDDEEFF)
        self.stage2.set_command_line("\x01" * (stage2.max_command_line_size - 1))
        raw = self.stage2.get_raw()
        conf = raw[2:282]
        self.assertEqual(raw[:2], "\x00\x00")
        self.assertEqual(raw[282:], "\x00" * 230)
        self.assertEqual(conf, "\xEF\xCD\xAB\x89\x67\x45\x23\x01\x77\x66\x55\x44\x33\x22\x11\x00\xBB\xAA\x99\x88\xFF\xEE\xDD\xCC" +
            "\x01" * (stage2.max_command_line_size - 1) + "\x00")
        self.assertEqual(self.stage2.get_kernel_blocklist_lba(), 0x0123456789ABCDEF)
        self.assertEqual(self.stage2.get_initrd_blocklist_lba(), 0x0011223344556677)
        self.assertEqual(self.stage2.get_command_line(), "\x01" * (stage2.max_command_line_size - 1))
