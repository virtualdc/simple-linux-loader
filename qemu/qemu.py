import gdbcli
import subprocess


class QemuGdbClient(gdbcli.GdbClient):

    def __init__(self, args = []):
        super(QemuGdbClient, self).__init__()
        args = ["qemu-system-i386", "-gdb", "stdio", "-vnc", "none",
            "-monitor", "none", "-S"] + args
        done, p = self.execute("target remote | exec " + " ".join(args))
        if done != "done":
            raise gdbcli.GdbError("Can't launch qemu")

    def close(self):
        self.execute("detach")
        super(QemuGdbClient, self).close()
