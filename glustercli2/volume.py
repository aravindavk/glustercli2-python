from glustercli2.parsers import parsed_volume_info, parsed_volume_status


class Volume:
    def __init__(self, cli, volume_name):
        self.cli = cli
        self.name = volume_name

    @classmethod
    def volume_cmd(cls, cli, cmd):
        return cli.exec_gluster_command(
            ["volume"] + cmd
        )

    def start(self, force=False):
        """
        == Volume Start

        Start the Volume.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1").start()

        # or using force option
        gcli.volume("gvol1").start(force=True)
        ----
        """
        cmd = ["start", self.name]

        if force:
            cmd.append("force")

        self.volume_cmd(self.cli, cmd)

    def stop(self, force=False):
        """
        == Volume Stop

        Stop the Volume.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1").stop()

        # or using force option
        gcli.volume("gvol1").stop(force=True)
        ----
        """
        cmd = ["stop", self.name]

        if force:
            cmd.append("force")

        self.volume_cmd(self.cli, cmd)

    def delete(self):
        """
        == Volume Delete

        Delete the Volume.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1").delete()
        ----
        """
        cmd = ["delete", self.name]
        self.volume_cmd(self.cli, cmd)

    @classmethod
    def _info(cls, cli, volume_name="all"):
        cmd = ["info"]
        if volume_name != "all":
            cmd.append(volume_name)

        out = cls.volume_cmd(cli, ["info"])
        return parsed_volume_info(out)

    @classmethod
    def _status(cls, cli, volume_name="all"):
        info = cls._info(cli, volume_name)
        out = cls.volume_cmd(cli, ["status", volume_name, "detail"])
        return parsed_volume_status(out, info)

    @classmethod
    def list(cls, cli, status=False):
        return cls._info(cli) if not status else cls._status(cli)

    def info(self, status=False):
        """
        == Volume Info and Status

        Get Volume info or Status.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1").info()
        gcli.volume("gvol1").info(status=True)
        ----
        """
        if not status:
            data = self._info(self.cli, self.name)
        else:
            data = self._status(self.cli, self.name)

        return data[0]

    def option_set(self, opts):
        """
        == Set Volume Option

        Set Volume Option.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1").option_set({
            "changelog.changelog": "on"
        })
        ----
        """
        cmd = ["set", self.name]
        for key, value in opts.items():
            cmd += [key, value]

        self.volume_cmd(self.cli, cmd)

    def option_reset(self, opts):
        """
        == Reset Volume Option

        Reset Volume Option.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1").option_reset(["changelog.changelog"])
        ----
        """
        cmd = ["set", self.name]
        cmd += opts

        self.volume_cmd(self.cli, cmd)

    @classmethod
    def create(cls, cli, name, bricks, opts):
        cmd = ["create", name]

        if opts.replica_count > 1:
            cmd += ["replica", opts.replica_count]

        if opts.disperse_count > 0:
            cmd += ["disperse", opts.disperse_count]

        if opts.disperse_redundancy_count > 0:
            cmd += ["redundancy", opts.disperse_redundancy_count]

        if opts.arbiter_count > 0:
            cmd += ["arbiter", opts.arbiter_count]

        cmd += bricks

        if opts.force:
            cmd.append("force")

        cls.volume_cmd(cli, cmd)
