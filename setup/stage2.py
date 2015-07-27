import struct


# offsets MUST correspond to config block in entry.asm and stage2.c
conf_header_size = 0
conf_kernel_blocklist_lba = 2
conf_initrd_blocklist_lba = 10
conf_command_line = 18
max_command_line_size = 256


class Stage2Error(Exception):
    pass


class Stage2(object):

    def __init__(self, stream):
        self.data = stream.read()

    def get_raw(self):
        return self.data

    def get_header_size(self):
        return conf_command_line + max_command_line_size

    def set_kernel_blocklist_lba(self, lba):
        self.set(conf_kernel_blocklist_lba, lba, 8)

    def get_kernel_blocklist_lba(self):
        return self.get(conf_kernel_blocklist_lba, 8)

    def set_initrd_blocklist_lba(self, lba):
        self.set(conf_initrd_blocklist_lba, lba, 8)

    def get_initrd_blocklist_lba(self):
        return self.get(conf_initrd_blocklist_lba, 8)

    def set_command_line(self, cmdline):
        if len(cmdline) >= max_command_line_size:
            raise Stage2Error("Command line too large")
        cmdline += "\x00" * (max_command_line_size - len(cmdline))
        self.data = (self.data[:conf_command_line] + cmdline +
            self.data[conf_command_line + max_command_line_size:])

    def get_command_line(self):
        cmdline = self.data[conf_command_line : conf_command_line+max_command_line_size]
        return cmdline.rstrip("\x00")

    def set(self, offset, value, size):
        bytes = []
        for i in xrange(0, size):
            bytes.append(chr(value & 0xFF))
            value >>= 8
        bytes = "".join(bytes)
        self.data = self.data[:offset] + bytes + self.data[offset+size:]

    def get(self, offset, size):
        bytes = self.data[offset:offset+size]
        out = 0
        shift = 0
        for b in bytes:
            out = out | (ord(b) << shift)
            shift += 8
        return out
