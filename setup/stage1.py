import struct


# offsets MUST correspond to config block in stage1.asm
conf_stack_ofs = 0
conf_stack_seg = 2
conf_stage2_ofs = 4
conf_stage2_seg = 6
conf_entry_ofs = 8
conf_entry_seg = 10
conf_blocklist_lba = 12
conf_size = 20 # total size


class Stage1(object):

    def __init__(self, stream):
        self.data = stream.read()

    def get_raw(self):
        return self.data

    def set_stack(self, (seg, ofs)):
        self.set(conf_stack_ofs, ofs, 2)
        self.set(conf_stack_seg, seg, 2)

    def get_stack(self):
        return (self.get(conf_stack_seg, 2), self.get(conf_stack_ofs, 2))

    def set_stage2(self, (seg, ofs)):
        self.set(conf_stage2_ofs, ofs, 2)
        self.set(conf_stage2_seg, seg, 2)

    def get_stage2(self):
        return (self.get(conf_stage2_seg, 2), self.get(conf_stage2_ofs, 2))

    def set_entry(self, (seg, ofs)):
        self.set(conf_entry_ofs, ofs, 2)
        self.set(conf_entry_seg, seg, 2)

    def get_entry(self):
        return (self.get(conf_entry_seg, 2), self.get(conf_entry_ofs, 2))

    def set_blocklist_lba(self, lba):
        self.set(conf_blocklist_lba, lba, 8)

    def get_blocklist_lba(self):
        return (self.get(conf_blocklist_lba, 8))

    def set(self, offset, value, size):
        offset = len(self.data) - conf_size + offset
        bytes = []
        for i in xrange(0, size):
            bytes.append(chr(value & 0xFF))
            value >>= 8
        bytes = "".join(bytes)
        self.data = self.data[:offset] + bytes + self.data[offset+size:]

    def get(self, offset, size):
        offset = len(self.data) - conf_size + offset
        bytes = self.data[offset:offset+size]
        out = 0
        shift = 0
        for b in bytes:
            out = out | (ord(b) << shift)
            shift += 8
        return out
