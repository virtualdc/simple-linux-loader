import unittest
import StringIO
import qemu
import mbr
import stage1
import blocklist
import os
import struct


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
            first, first_size = wr.put_data(payload)
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
