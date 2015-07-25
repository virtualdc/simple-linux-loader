import unittest
import qemu


class TestEmptyImage(unittest.TestCase):

    def setUp(self):
        self.qemu = qemu.QemuGdbClient()

    def tearDown(self):
        self.qemu.close()

    def test_code_exec(self):
        code = "\x66\xB8\x67\x45\x23\x01" # mov eax, 0x12345678
        self.qemu.set_reg("eax", 0xDEADC0DE)
        self.assertEqual(self.qemu.get_reg("eax"), 0xDEADC0DE)
        self.qemu.set_mem(0x0600, code)
        self.qemu.set_reg("cs", 0x0060)
        self.qemu.set_reg("eip", 0x0000)
        self.qemu.set_breakpoint(0x0606)
        self.qemu.run()
        self.assertEqual(self.qemu.get_reg("eax"), 0x01234567)


class TestDummyImage(unittest.TestCase):

    def setUp(self):
        self.qemu = qemu.QemuGdbClient(["-fda", "./qemu-dummy.bin"])

    def tearDown(self):
        self.qemu.close()

    def test_code_exec(self):
        self.qemu.set_breakpoint(0x7C06)
        self.qemu.run()
        self.assertEqual(self.qemu.get_reg("eax"), 0x01234567)
