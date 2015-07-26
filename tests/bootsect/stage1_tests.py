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


class TestStage1Code(unittest.TestCase):

    def setUp(self):
        self.mbr = mbr.MBR()
        with open("mbr.bin", "r") as f:
            self.mbr.load(f)
        with open("mbr.map", "r") as f:
            self.mbr.load_map(f)
        with open("stage1.bin", "r") as f:
            self.stage1 = stage1.Stage1(f)
        self.qemu = None

    def tearDown(self):
        if self.qemu:
            self.qemu.close()

    def run_and_check_payload(self, sectors):
        payload = []
        for i in xrange(0, sectors):
            payload.append(chr(i+10) * 512)
        payload = "".join(payload)

        testbin = "stage1-test.bin"

        with open(testbin, "w") as f:
            f.write("\x00" * 512)
            wr = blocklist.BlockWriter(f, 1)
            first = wr.put_data(payload)
            f.seek(0)
            self.stage1.set_stack((0x0000, 0x1000))
            self.stage1.set_stage2((0x0100, 0x0000))
            self.stage1.set_entry((0x0100, 0x0003))
            self.stage1.set_blocklist_lba(first)
            self.mbr.set_payload(self.stage1.get_raw())
            self.mbr.save(f)

        self.qemu = qemu.QemuGdbClient(["-hda", testbin])
        self.qemu.set_breakpoint(0x01003)
        self.qemu.run()
        self.assertEqual(self.qemu.get_reg("ss"), 0x0000)
        self.assertEqual(self.qemu.get_reg("esp"), 0x1000)
        self.assertEqual(self.qemu.get_mem(0x1000, 512 * sectors), payload)

    def test_2_sectors(self):
        self.run_and_check_payload(2)

    def test_63_sectors(self):
        self.run_and_check_payload(63)

    def test_64_sectors(self):
        self.run_and_check_payload(64)
