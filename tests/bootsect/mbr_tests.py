import unittest
import StringIO
import qemu
import mbr
import os


class TestMbrCode(unittest.TestCase):

    def setUp(self):
        self.payload = "".join(map(chr,xrange(1, 200)))
        m = mbr.MBR()
        with open("mbr.bin", "r") as f:
            m.load(f)
        with open("mbr.map", "r") as f:
            m.load_map(f)
        m.set_payload(self.payload)
        testbin = "mbr-test.bin"
        with open(testbin, "w") as f:
            m.save(f)
        self.qemu = qemu.QemuGdbClient(["-hda", testbin])

    def tearDown(self):
        self.qemu.close()

    def test_mbr_code(self):
        self.qemu.set_breakpoint(0x0500)
        self.qemu.run()
        mem = self.qemu.get_mem(0x0500, len(self.payload))
        self.assertEqual(mem, self.payload)
        self.assertEqual(self.qemu.get_reg("cs"), 0x0050)
        self.assertEqual(self.qemu.get_reg("eip"), 0x0000)
        self.assertEqual(self.qemu.get_reg("edx") & 0xFF, 0x80)
