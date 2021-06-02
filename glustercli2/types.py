import json

class CommandOutputParseError(Exception):
    pass

class Info:
    def is_class(self, value):
        return hasattr(value, "__dict__") and hasattr(value, "__class__")

    def is_list(self, value):
        return hasattr(value, "__iter__")  and not isinstance(value, str)

    def list_to_dict(self, value):
        values = []
        for val in value:
            if self.is_class(val):
                values.append(self.cls_to_dict(val))
            elif self.is_list(val):
                values.append(self.list_to_dict(val))
            else:
                values.append(val)

        return values

    def cls_to_dict(self, value):
        vals = {}
        for key, val in value.__dict__.items():
            if self.is_class(val):
                vals[key] = self.cls_to_dict(val)
            elif self.is_list(val):
                vals[key] = self.list_to_dict(val)
            else:
                vals[key] = val

        return vals

    def to_json(self):
        data = self.__dict__
        outdata = self.cls_to_dict(self)
        return json.dumps(outdata)

    def __str__(self):
        outstr = []
        for key, value in self.__dict__.items():
            outstr.append(f"{key}=\"{value}\"")
        return " ".join(outstr)


class NodeInfo(Info):
    def __init__(self):
        self.id = ""
        self.hostname = ""
        self.state = "Disconnected"


class PortsInfo(Info):
    def __init__(self):
        self.tcp = 0
        self.rdma = 0


class BrickInfo(Info):
    def __init__(self):
        self.node = NodeInfo()
        self.path = ""
        self.type = "Brick"
        self.state = "Unknown"
        self.pid = 0
        self.size_total = 0
        self.size_free = 0
        self.inodes_total = 0
        self.inodes_free = 0
        self.size_used = 0
        self.inodes_used = 0
        self.device = ""
        self.block_size = 0
        self.fs_name = ""
        self.mnt_options = ""
        self.ports = PortsInfo()


class SubvolInfo(Info):
    def __init__(self):
      self.type = ""
      self.health = ""
      self.replica_count = 0
      self.disperse_count = 0
      self.disperse_redundancy_count = 0
      self.arbiter_count = 0
      self.size_total = 0
      self.size_free = 0
      self.inodes_total = 0
      self.inodes_free = 0
      self.size_used = 0
      self.inodes_used = 0
      self.up_bricks = 0
      self.bricks = []

class OptionInfo(Info):
    def __init__(self):
        self.name = ""
        self.value = ""


class VolumeInfo(Info):
    def __init__(self):
      self.name = ""
      self.id = ""
      self.state = ""
      self.snapshot_count = 0
      self.bricks_count = 0
      self.distribute_count = 0
      self.replica_count = 0
      self.arbiter_count = 0
      self.disperse_count = 0
      self.disperse_redundancy_count = 0
      self.type = ""
      self.health = ""
      self.transport = ""
      self.size_total = 0
      self.size_free = 0
      self.inodes_total = 0
      self.inodes_free = 0
      self.size_used = 0
      self.inodes_used = 0
      self.up_subvols = 0
      self.subvols = []
      self.options = []

class VolumeCreateOptions:
    def __init__(self):
        self.replica_count = 1
        self.disperse_count = 0
        self.disperse_redundancy_count = 0
        self.arbiter_count = 0
        self.force = False
