import re


sector_size = 512
partition_table_offset = 0x1BE
partition_entry_size = 16
partition_entry_count = 4


class MBRError(Exception):
    pass


class MBR(object):

    def __init__(self):
        self.mbr = None
        self.payload_begin = None
        self.payload_end = None

    def load(self, stream):
        mbr = stream.read(sector_size)
        if len(mbr) != sector_size:
            raise MBRError("Not enough bytes in input stream")
        self.mbr = mbr

    def save(self, stream):
        if self.mbr is None:
            raise MBRError("Nothing to save")
        stream.write(self.mbr)

    def load_map(self, stream):
        for line in stream:
            m = re.match(r"\s*([0-9A-Fa-f]+)\s*([0-9A-Fa-f]+)\s*([0-9A-Za-z_]+)", line)
            if m:
                real = m.group(1)
                virtual = m.group(2)
                name = m.group(3)
                if name == "payload_begin":
                    self.payload_begin = int(virtual, 16)
                if name == "payload_end":
                    self.payload_end = int(virtual, 16)
        if self.payload_begin is None or self.payload_end is None:
            raise MBRError("Can't find payload location in map")

    def max_payload_size(self):
        if self.payload_begin is None or self.payload_end is None:
            raise MBRError("Map must be loaded")
        return self.payload_end - self.payload_begin

    def set_payload(self, payload):
        if self.mbr is None:
            raise MBRError("MBR must be loaded")
        if len(payload) > self.max_payload_size():
            raise MBRError("Payload too large")
        self.mbr = self.mbr[:self.payload_begin] + payload + self.mbr[self.payload_begin + len(payload):]

    def get_partition_table(self):
        if self.mbr is None:
            raise MBRError("MBR must be loaded")
        offset = partition_table_offset
        buf = []
        for i in xrange(0, partition_entry_count):
            buf.append(PartitionInfo(self.mbr[offset:offset+partition_entry_size]))
            offset += partition_entry_size
        return buf

    def set_partition_table(self, partitions):
        if self.mbr is None:
            raise MBRError("MBR must be loaded")
        if len(partitions) != partition_entry_count:
            raise MBRError("Partition table must contain {0} entries".format(partition_entry_count))
        buf = []
        for part in partitions:
            raw = part.get_raw()
            if len(raw) != partition_entry_size:
                raise MBRError("Bad partition entry size")
            buf.append(raw)
        buf = "".join(buf)
        self.mbr = self.mbr[:partition_table_offset] + buf + self.mbr[partition_table_offset + len(buf):]


# TODO: parse partitions
class PartitionInfo(object):

    def __init__(self, raw):
        self.raw = raw

    def get_raw(self):
        return self.raw
