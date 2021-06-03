import subprocess

from glustercli2.peer import Peer
from glustercli2.volume import Volume

DEFAULT_SSH_PORT = 22
DEFAULT_SSH_USER = "root"
DEFAULT_SSH_KEY = "/root/.ssh/id_rsa"
DEFAULT_SSH_USE_SUDO = False


def execute(cmd):
    with subprocess.Popen(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True
                          ) as proc:
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise CommandException(proc.returncode, err.strip())

        return out.strip()


class CommandException(Exception):
    pass


# noqa # pylint: disable=too-many-instance-attributes
class GlusterCLI:
    def __init__(self, exec_path="gluster", current_host="", socket_path=""):
        """
        == Gluster CLI instance.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        # With default Options
        gcli = GlusterCLI()

        # With custom gluster executable path
        gcli = GlusterCLI(exec_path="/usr/local/sbin/gluster")

        # Set Current Host to replace `localhost` in Peers list output
        gcli = GlusterCLI(current_host="server1.kadalu")

        # Set Glusterd socket Path
        gcli = GlusterCLI(
            exec_path="/usr/local/sbin/gluster",
            current_host="server1.kadalu",
            socket_path="/usr/local/var/run/glusterd.sock"
        )
        ----
        """
        self.exec_path = exec_path
        self.current_host = current_host
        self.socket_path = socket_path
        self.remote_plugin = "local"
        self.remote_host = ""
        self.ssh_port = DEFAULT_SSH_PORT
        self.ssh_user = DEFAULT_SSH_USER
        self.ssh_key = DEFAULT_SSH_KEY
        self.ssh_use_sudo = DEFAULT_SSH_USE_SUDO

    def _set_remote_plugin(self, name):
        # Validate name: local|ssh|docker
        self.remote_plugin = name

    def set_container_name(self, name):
        """
        == Docker exec

        Set Remote plugin as docker and set the container name

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.set_container_name("server1.kadalu")
        ----
        """
        self._set_remote_plugin("docker")
        self.remote_host = name

    # noqa # pylint: disable=too-many-arguments
    def set_ssh_params(self, hostname, port=DEFAULT_SSH_PORT,
                       user=DEFAULT_SSH_USER, key=DEFAULT_SSH_KEY,
                       use_sudo=DEFAULT_SSH_USE_SUDO):
        """
        == Execute over SSH

        Set Remote plugin as ssh and set the SSH parameters

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.set_ssh_params(
            "remote1.kadalu",
            port=22,
            user="root",
            key="/root/.ssh/id_rsa",
            use_sudo=False
        )
        ----
        """
        self._set_remote_plugin("ssh")
        self.remote_host = hostname
        self.ssh_port = port
        self.ssh_user = user
        self.ssh_key = key
        self.ssh_use_sudo = use_sudo

    def get_current_host(self):
        if self.current_host != "":
            return self.current_host

        cmd = self._full_command(["hostname"])
        return execute(cmd).strip()

    def _full_command(self, cmd):
        if self.remote_plugin == "docker":
            return [
                "docker", "exec", "-i", self.remote_host,
                "/bin/bash", "-c", " ".join(cmd)
            ]

        if self.remote_plugin == "ssh":
            full_cmd = [
                "ssh",
                "-oStrictHostKeyChecking=no",
                f"-p{self.ssh_port}",
                "-i", self.ssh_key,
                f"{self.ssh_user}@{self.remote_host}"
            ]

            if self.ssh_use_sudo:
                full_cmd.append("sudo")

            full_cmd += cmd
            return full_cmd

        return cmd

    def exec_gluster_command(self, cmd, xml=True):
        # TODO: Set Socket path
        gcmd = [self.exec_path, "--mode=script"]

        if self.socket_path != "":
            gcmd.append(f"--glusterd-sock={self.socket_path}")

        if xml:
            gcmd.append("--xml")

        gcmd += cmd
        return execute(self._full_command(gcmd))

    def version(self):
        """
        == GlusterFS Version

        Return the GlusterFS version

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        print(gcli.version())
        ----
        """
        cmd = [self.exec_path, "--version"]
        out = execute(self._full_command(cmd))
        return out.split("\n")[0]

    def list_peers(self):
        """
        == Peers List

        List Peers available.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.list_peers()
        ----
        """
        return Peer.list(self)

    def list_volumes(self, status=False):
        """
        == Volumes List and Status

        List Volumes available.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.list_volumes()
        gcli.list_volumes(status=True)
        ----
        """
        return Volume.list(self, status)

    def volume(self, volume_name):
        """
        == Get Volume instance.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.volume("gvol1")
        ----
        """
        return Volume(self, volume_name)

    def peer(self, hostname):
        """
        == Get Peer instance.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.peer("server2.kadalu")
        ----
        """
        return Peer(self, hostname)

    def add_peer(self, hostname):
        """
        == Peer Add/Probe

        Add a Peer to Cluster.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI

        gcli = GlusterCLI()
        gcli.add_peer("server2.kadalu")
        ----
        """
        Peer.add(self, hostname)

    def create_volume(self, name, bricks, opts):
        """
        == Volume Create

        Create a Volume.

        Example:

        [source,python]
        ----
        from glustercli2 import GlusterCLI, VolumeCreateOptions

        gcli = GlusterCLI()
        opts = VolumeCreateOptions()
        opts.replica_count = 3
        opts.force = True

        bricks = [
            "server1.kadalu:/bricks/gvol1/brick1/brick",
            "server2.kadalu:/bricks/gvol1/brick2/brick",
            "server3.kadalu:/bricks/gvol1/brick3/brick"
        ]

        gcli.create_volume("gvol1", bricks, opts)
        ----
        """
        Volume.create(self, name, bricks, opts)
