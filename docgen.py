import sys

from glustercli2 import GlusterCLI
from glustercli2.peer import Peer
from glustercli2.volume import Volume


def print_doc(doc):
    for line in doc.split("\n"):
        print(line.replace(" "*8, ""))


def get_doc(cls):
    for meth in dir(cls):
        if meth.startswith("_"):
            continue

        doc = getattr(cls, meth).__doc__
        if doc == "" or doc is None:
            continue

        print_doc(doc)


print("= GlusterCLI - Python bindings for GlusterFS Commands")
print()
print_doc(GlusterCLI.__init__.__doc__)
get_doc(GlusterCLI)
get_doc(Volume)
get_doc(Peer)
