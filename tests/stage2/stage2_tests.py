import unittest
import StringIO
import qemu
import struct
import builder


class TestStage2Launch(unittest.TestCase):

    def setUp(self):
        testbin = "stage2-test.bin"

        builder.build_stage2_image(testbin, stage2 = "stage2.bin")

        self.qemu = qemu.QemuGdbClient(["-hda", testbin])
        self.qemu.execute("symbol-file stage2.elf")

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
        main = self.qemu.address_of("stage2_main")
        self.qemu.set_breakpoint(main)
        self.qemu.run()
        self.assertEqual(self.qemu.get_reg("cs"), 0x10)
        for sreg in ["ds", "es", "fs", "gs", "ss"]:
            self.assertEqual(self.qemu.get_reg(sreg), 0x18)
        esp = self.qemu.get_reg("esp")
        self.assertEqual(esp, 0x1000 - 8)
        self.assertEqual(struct.unpack("<I", self.qemu.get_mem(esp+4, 4))[0], 0x80)
