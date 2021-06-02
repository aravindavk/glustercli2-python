from .parsers import parsed_pool_list


class Peer:
    def __init__(self, cli, hostname):
        self.cli = cli
        self.hostname = hostname

    @classmethod
    def peer_cmd(cls, cli, cmd):
        return cli.exec_gluster_command(
            ["peer"] + cmd
        )

    @classmethod
    def list(cls, cli):
        out = cli.exec_gluster_command(["pool", "list"])
        return parsed_pool_list(out)

    @classmethod
    def add(cls, cli, hostname):
        self.peer_cmd(cli, ["attach", hostname])

    def detach(self):
        self.peer_cmd(self.cli, ["detach", self.hostname])
