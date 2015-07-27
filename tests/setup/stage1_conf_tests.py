import unittest
import StringIO
import qemu
import mbr
import stage1
import blocklist
import os
import struct


class TestStage1Builder(unittest.TestCase):

    def setUp(self):
        f = StringIO.StringIO("\x00" * 256)
        self.stage1 = stage1.Stage1(f)

    def test_get_set(self):
        self.stage1.set_stack((0x0123, 0x4567))
        self.stage1.set_stage2((0x89AB, 0xCDEF))
        self.stage1.set_entry((0x0011, 0x2233))
        self.stage1.set_blocklist_lba(0x445566778899AABB)
        raw = self.stage1.get_raw()
        conf = raw[-20:]
        self.assertEqual(raw[:-20], "\x00" * 236)
        self.assertEqual(conf, "\x67\x45\x23\x01\xEF\xCD\xAB\x89\x33\x22\x11\x00\xBB\xAA\x99\x88\x77\x66\x55\x44")
        self.assertEqual(self.stage1.get_stack(), (0x0123, 0x4567))
        self.assertEqual(self.stage1.get_stage2(), (0x89AB, 0xCDEF))
        self.assertEqual(self.stage1.get_entry(), (0x0011, 0x2233))
        self.assertEqual(self.stage1.get_blocklist_lba(), 0x445566778899AABB)
