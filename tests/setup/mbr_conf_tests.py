import unittest
import StringIO
import qemu
import mbr
import os


class TestMbrBuilder(unittest.TestCase):

    def setUp(self):
        self.mbr = mbr.MBR()
        f = StringIO.StringIO("\x01" * 512)
        self.mbr.load(f)
        f = StringIO.StringIO("  10 10 payload_begin\n30 30 payload_end")
        self.mbr.load_map(f)

    def test_short_stream(self):
        f = StringIO.StringIO("\x01" * 511)
        with self.assertRaises(mbr.MBRError):
            self.mbr.load(f)

    def test_save(self):
        f = StringIO.StringIO()
        self.mbr.save(f)
        data = f.getvalue()
        self.assertEqual(data, "\x01" * 512)

    def test_payload_size(self):
        self.assertEqual(self.mbr.max_payload_size(), 32)

    def test_payload(self):
        max_size = self.mbr.max_payload_size()
        payload = "\x02" * max_size
        self.mbr.set_payload(payload)
        f = StringIO.StringIO()
        self.mbr.save(f)
        data = f.getvalue()
        self.assertEqual(data, "\x01" * 16 + "\x02" * 32 + "\x01" * 464)

    def test_large_payload(self):
        max_size = self.mbr.max_payload_size()
        payload = "\x02" * (max_size + 1)
        with self.assertRaises(mbr.MBRError):
            self.mbr.set_payload(payload)

    def test_partitions(self):
        partitions = []
        for i in xrange(0, 4):
            partitions.append(mbr.PartitionInfo(chr(10 + i) * 16))
        self.mbr.set_partition_table(partitions)
        f = StringIO.StringIO()
        self.mbr.save(f)
        data = f.getvalue()
        self.assertEqual(data, "\x01" * 0x1BE + "\x0A" * 16 + "\x0B" * 16 +
            "\x0C" * 16 + "\x0D" * 16 + "\x01\x01")
        p = self.mbr.get_partition_table()
        for i in xrange(0, 4):
            self.assertEqual(p[i].get_raw(), chr(10 + i) * 16)
