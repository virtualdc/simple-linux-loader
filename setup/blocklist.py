import struct


sector_size = 512
record_size = 8


class BlockWriter(object):

    def __init__(self, stream, sector):
        self.stream = stream
        self.sector = sector
        self.records = []

    def put_sector(self, data):
        self.stream.write(data)
        sector = self.sector
        self.sector += 1
        return sector

    def put_blocklist_record(self, sector):
        if len(self.records) == sector_size / record_size - 1:
            self.records.append(struct.pack("<Q", self.sector + 1))
            self.put_sector("".join(self.records))
            self.records = []
        self.records.append(struct.pack("<Q", sector))

    def terminate_blocklist(self):
        self.records.append("\xFF" * 8)
        data = "".join(self.records)
        size = len(data)
        if size % sector_size != 0:
            data += "\x00" * (sector_size - size % sector_size)
        self.put_sector(data)
        self.records = []

    def put_data(self, data):
        # pad data
        size = len(data)
        if size % sector_size != 0:
            data += "\x00" * (sector_size - size % sector_size)
        sector_count = len(data) / sector_size
        # write data sectors
        sectors = []
        for i in xrange(0, sector_count):
            chunk = data[i*sector_size:(i+1)*sector_size]
            sectors.append(self.put_sector(chunk))
        # write blocklist
        first = self.sector
        for sector in sectors:
            self.put_blocklist_record(sector)
        self.terminate_blocklist()
        return (first, sector_count * sector_size)
