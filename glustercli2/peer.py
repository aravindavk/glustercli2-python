from glustercli2.parsers import parsed_pool_list


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
        cls.peer_cmd(cli, ["attach", hostname])

    def detach(self):
        """
        == Peer Delete/Detach

        Delete or Detach a Peer from Cluster.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.peer("server2.kadalu").delete()
        ----
        """
        self.peer_cmd(self.cli, ["detach", self.hostname])
