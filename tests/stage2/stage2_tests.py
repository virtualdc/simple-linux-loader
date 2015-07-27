import unittest
import StringIO
import qemu
import mbr
import stage1
import blocklist
import os
import struct


class TestStage2Launch(unittest.TestCase):

    def setUp(self):
        testbin = "stage2-test.bin"

        with open("stage2.bin", "r") as f:
            s2 = f.read()

        with open("stage1.bin", "r") as f:
            s1 = stage1.Stage1(f)

        m = mbr.MBR()
        with open("mbr.bin", "r") as f:
            m.load(f)
        with open("mbr.map", "r") as f:
            m.load_map(f)

        with open(testbin, "w") as f:
            f.write("\x00" * 512)
            wr = blocklist.BlockWriter(f, 1)
            stage2_lba = wr.put_data(s2)

            s1.set_stack((0x0000, 0x1000))
            s1.set_stage2((0x0100, 0x0000))
            s1.set_entry((0x0100, 0x0000))
            s1.set_blocklist_lba(stage2_lba)
            m.set_payload(s1.get_raw())

            f.seek(0)
            m.save(f)

        self.qemu = qemu.QemuGdbClient(["-hda", testbin])
        self.qemu.execute("symbol-file stage2.sym")

    def tearDown(self):
        self.qemu.close()

    def test_entry_break(self):
        entry = self.qemu.address_of("stage2_entry")
        self.qemu.set_breakpoint(entry)
        self.qemu.run()

    def test_pm_switch(self):
        pm = self.qemu.address_of("stage2_pm")
        self.qemu.set_breakpoint(pm)
        self.qemu.run()
        self.assertEqual(self.qemu.get_reg("cs"), 0x10)
        self.assertEqual(self.qemu.get_reg("eip"), self.qemu.address_of("stage2_pm"))

    def test_main_call(self):
        main = self.qemu.address_of("main")
        self.qemu.set_breakpoint(main)
        self.qemu.run()
        self.assertEqual(self.qemu.get_reg("cs"), 0x10)
        for sreg in ["ds", "es", "fs", "gs", "ss"]:
            self.assertEqual(self.qemu.get_reg(sreg), 0x18)
        esp = self.qemu.get_reg("esp")
        self.assertEqual(esp, 0x1000 - 8)
        self.assertEqual(struct.unpack("<I", self.qemu.get_mem(esp+4, 4))[0], 0x80)
