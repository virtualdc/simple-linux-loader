import unittest
import struct
import StringIO
import blocklist


class TestBlockWriter(unittest.TestCase):

    def setUp(self):
        self.stream = StringIO.StringIO()
        self.stream.write("\x00" * 512)
        self.bw = blocklist.BlockWriter(self.stream, 1)

    def test_padding(self):
        data = "\x01" * 511
        self.assertEqual(self.bw.put_data(data), 2)
        self.assertEqual(self.stream.getvalue(),
            "\x00" * 512 +
            "\x01" * 511 + "\x00" +
            "\x01" + "\x00" * 7 + "\xFF" * 8 + "\x00" * 62 * 8)

    def test_no_padding(self):
        data = "\x01" * 512
        self.assertEqual(self.bw.put_data(data), 2)
        self.assertEqual(self.stream.getvalue(),
            "\x00" * 512 +
            "\x01" * 512 +
            "\x01" + "\x00" * 7 + "\xFF" * 8 + "\x00" * 62 * 8)

    def test_63_sectors(self):
        data = "\x01" * 512 * 63
        self.assertEqual(self.bw.put_data(data), 64)
        buf = []
        buf.append("\x00" * 512)
        buf.append("\x01" * 512 * 63)
        for i in xrange(0, 63):
            buf.append(struct.pack("<Q", i + 1))
        buf.append("\xFF" * 8)
        self.assertEqual(self.stream.getvalue(), "".join(buf))

    def test_64_sectors(self):
        data = "\x01" * 512 * 64
        self.assertEqual(self.bw.put_data(data), 65)
        buf = []
        buf.append("\x00" * 512)
        buf.append("\x01" * 512 * 64)
        for i in xrange(0, 63):
            buf.append(struct.pack("<Q", i + 1))
        buf.append(struct.pack("<Q", 66))
        buf.append(struct.pack("<Q", 64))
        buf.append("\xFF" * 8)
        buf.append("\x00" * 8 * 62)
        self.assertEqual(self.stream.getvalue(), "".join(buf))
