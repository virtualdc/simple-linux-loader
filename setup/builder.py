from blocklist import BlockWriter
from mbr import MBR
from stage1 import Stage1
from stage2 import Stage2


def build_image(out, mbr = "mbr.bin", mbr_map = "mbr.map", stage1 = "stage1.bin",
        stage2 = "stage2.bin", s2_load = (0x0000, 0x1000),
        s2_stack = (0x0000, 0x1000), kernel = None, initrd = None, cmdline = "auto"):

    m = MBR()
    with open(mbr, "r") as f:
        m.load(f)
    with open(mbr_map, "r") as f:
        m.load_map(f)

    with open(stage1, "r") as f:
        s1 = Stage1(f)

    with open(stage2, "r") as f:
        s2 = Stage2(f)

    with open(out, "w") as f:
        # reserve first sector
        m.save(f)

        bw = BlockWriter(f, 1)

        # put kernel to image
        if kernel:
            with open(kernel, "r") as f:
                kernel_raw = f.read()
            kernel_lba = bw.put_data(kernel_raw)
        else:
            kernel_lba = 0xFFFFFFFFFFFFFFFF

        # put initrd to image
        if initrd:
            with open(initrd, "r") as f:
                initrd_raw = f.read()
            initrd_lba = bw.put_data(initrd_raw)
        else:
            initrd_lba = 0xFFFFFFFFFFFFFFFF

        # configure stage2
        s2.set_kernel_blocklist_lba(kernel_lba)
        s2.set_initrd_blocklist_lba(initrd_lba)
        s2.set_command_line(cmdline)

        # put stage2 to image
        s2_lba = bw.put_data(s2.get_raw())

        # configure stage1
        s1.set_stage2(s2_load)
        s1.set_stack(s2_stack)
        s1.set_entry((s2_load[0], s2_load[1] + s2.get_header_size()))
        s1.set_blocklist_lba(s2_lba)

        # put stage1 to mbr
        m.set_payload(s1.get_raw())

        # put mbr to image
        f.seek(0)
        m.save(f)
