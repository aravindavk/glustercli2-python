import subprocess

from .peer import Peer
from .volume import Volume


class CommandException(Exception):
    pass


class GlusterCLI:
    def __init__(self, exec_path="gluster", current_host="", socket_path=""):
        self.exec_path = exec_path
        self.current_host = current_host
        self.socket_path = socket_path
        self.remote_plugin = "local"

    def set_remote_plugin(self, name):
        # Validate name: local|ssh|docker
        self.remote_plugin = name

    def set_container_name(self, name):
        self.set_remote_plugin("docker")
        self.remote_host = name

    def set_ssh_params(self, hostname, port=22, user="root", key="/root/.ssh/id_rsa", use_sudo=False):
        self.set_remote_plugin("ssh")
        self.remote_host = hostname
        self.ssh_port = port
        self.ssh_user = user
        self.ssh_key = key
        self.ssh_use_sudo = use_sudo

    def full_command(self, cmd):
        if self.remote_plugin == "local":
            return cmd

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

    def execute(self, cmd):
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise CommandException(proc.returncode, err.strip())

        return out.strip()

    def exec_gluster_command(self, cmd, xml=True):
        # TODO: Set Socket path
        gcmd = [self.exec_path, "--mode=script"]

        if xml:
            gcmd.append("--xml")

        gcmd += cmd
        return self.execute(self.full_command(gcmd))
    
    def list_peers(self):
        return Peer.list(self)

    def list_volumes(self, status=False):
        return Volume.list(self, status)

    def volume(self, volume_name):
        return Volume(self, volume_name)

    def add_peer(self, hostname):
        Peer.add(self, hostname)

    def create_volume(self, name, bricks, opts):
        Volume.create(self, name, bricks, opts)
