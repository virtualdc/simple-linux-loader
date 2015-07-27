from blocklist import BlockWriter
from mbr import MBR
from stage1 import Stage1


def build_stage2_image(out, mbr = "mbr.bin", mbr_map = "mbr.map", stage1 = "stage1.bin",
        stage2 = "stage2.bin", s2_load = (0x0000, 0x1000),
        s2_stack = (0x0000, 0x1000), s2_entry = (0x0000, 0x1000)):

    m = MBR()
    with open(mbr, "r") as f:
        m.load(f)
    with open(mbr_map, "r") as f:
        m.load_map(f)

    with open(stage1, "r") as f:
        s1 = Stage1(f)

    with open(stage2, "r") as f:
        s2 = f.read()

    with open(out, "w") as f:
        m.save(f)

        bw = BlockWriter(f, 1)
        s2_lba = bw.put_data(s2)

        s1.set_stage2(s2_load)
        s1.set_stack(s2_stack)
        s1.set_entry(s2_entry)
        s1.set_blocklist_lba(s2_lba)

        m.set_payload(s1.get_raw())

        f.seek(0)
        m.save(f)

