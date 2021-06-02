from .parsers import parsed_volume_info, parsed_volume_status


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
        cmd = ["start", self.name]

        if force:
            cmd.append("force")

        self.volume_cmd(self.cli, cmd)

    def stop(self, force=False):
        cmd = ["stop", self.name]

        if force:
            cmd.append("force")

        self.volume_cmd(self.cli, cmd)

    def delete(self):
        cmd = ["delete", self.name]

        if force:
            cmd.append("force")

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
        if not status:
            data = self._info(cli, self.name)
        else:
            data = self._status(cli, self.name)

        return data[0]

    def option_set(self, cli, opts):
        cmd = ["set", self.name]
        for k, v in opts.items():
            cmd += [k, v]

        cls.volume_cmd(cli, cmd)

    def option_reset(self, cli, opts):
        cmd = ["set", self.name]
        cmd += opts

        cls.volume_cmd(cli, cmd)

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
