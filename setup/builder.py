from blocklist import BlockWriter
from mbr import MBR
from stage1 import Stage1
from stage2 import Stage2
import argparse


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
            with open(kernel, "r") as g:
                kernel_raw = g.read()
            kernel_lba, kernel_size = bw.put_data(kernel_raw)
        else:
            kernel_lba, kernel_size = 0xFFFFFFFFFFFFFFFF, 0

        # put initrd to image
        if initrd:
            with open(initrd, "r") as g:
                initrd_raw = g.read()
            initrd_lba, initrd_size = bw.put_data(initrd_raw)
        else:
            initrd_lba, initrd_size = 0xFFFFFFFFFFFFFFFF, 0


        # configure stage2
        s2.set_kernel_blocklist_lba(kernel_lba)
        s2.set_initrd_blocklist_lba(initrd_lba)
        s2.set_kernel_size(kernel_size)
        s2.set_initrd_size(initrd_size)
        s2.set_command_line(cmdline)

        # put stage2 to image
        s2_lba, s2_size = bw.put_data(s2.get_raw())

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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Builds image with loader, kernel and initrd')
    parser.add_argument('--out', type=str, required=True)
    parser.add_argument('--mbr', type=str, required=True)
    parser.add_argument('--mbrmap', type=str, required=True)
    parser.add_argument('--stage1', type=str, required=True)
    parser.add_argument('--stage2', type=str, required=True)
    parser.add_argument('--kernel', type=str, default=None)
    parser.add_argument('--initrd', type=str, default=None)
    parser.add_argument('--cmdline', type=str, default="auto")
    args = parser.parse_args()

    build_image(args.out, mbr = args.mbr, mbr_map = args.mbrmap, stage1 = args.stage1,
        stage2 = args.stage2, kernel = args.kernel, initrd = args.initrd, cmdline = args.cmdline)
