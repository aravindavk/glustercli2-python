import math
import xml.etree.cElementTree as etree

from glustercli2.types import (
    NodeInfo, CommandOutputParseError, VolumeInfo,
    SubvolInfo, BrickInfo, OptionInfo
)

ParseError = etree.ParseError if hasattr(etree, 'ParseError') else SyntaxError

HEALTH_UP = "up"
HEALTH_DOWN = "down"
HEALTH_PARTIAL = "partial"
HEALTH_DEGRADED = "degraded"

STATE_CREATED = "Created"
STATE_STARTED = "Started"
STATE_STOPPED = "Stopped"

TYPE_REPLICATE = "Replicate"
TYPE_DISPERSE = "Disperse"


def parsed_pool_list(data):
    tree = etree.fromstring(data)
    pools = []
    for peer_el in tree.findall('peerStatus/peer'):
        try:
            peer = NodeInfo()
            peer.id = peer_el.find('uuid').text
            peer.hostname = peer_el.find('hostname').text
            if peer_el.find('connected').text == "1":
                peer.state = "Connected"

            pools.append(peer)
        except (ParseError, AttributeError, ValueError) as err:
            raise CommandOutputParseError from err

    return pools


def _subvol_health(subvol):
    up_bricks = 0
    for brick in subvol.bricks:
        if brick.state == "Online":
            up_bricks += 1

    health = HEALTH_UP
    if len(subvol.bricks) != up_bricks:
        health = HEALTH_DOWN
        # noqa # pylint: disable=c-extension-no-member
        if subvol.type == TYPE_REPLICATE and \
          up_bricks >= math.ceil(subvol.replica_count/2):
            health = HEALTH_PARTIAL

        # If down bricks are less than or equal to redudancy count
        # then Volume is UP but some bricks are down
        if subvol.type == TYPE_DISPERSE and \
          (len(subvol.bricks) - up_bricks) <= subvol.disperse_redundancy_count:
            health = HEALTH_PARTIAL

    return health


def _update_volume_health(volumes):
    # Note: vol is edited inside loop
    for vol in volumes:
        if vol.state != STATE_STARTED:
            continue

        vol.health = HEALTH_UP
        up_subvols = 0

        # Note: subvol is edited inside loop
        for subvol in vol.subvols:
            subvol.health = _subvol_health(subvol)

            if subvol.health == HEALTH_DOWN:
                vol.health = HEALTH_DEGRADED

            if subvol.health == HEALTH_PARTIAL and \
              vol.health != HEALTH_DEGRADED:
                vol.health = subvol.health

            if subvol.health != HEALTH_DOWN:
                up_subvols += 1

        if up_subvols == 0:
            vol.health = HEALTH_DOWN


def _update_volume_utilization(volumes):
    # Note: modifies volume inside loop
    for vol in volumes:
        # Note: modifies subvol inside loop
        for subvol in vol.subvols:
            effective_capacity_used = 0
            effective_capacity_total = 0
            effective_inodes_used = 0
            effective_inodes_total = 0

            for brick in subvol.bricks:
                if brick.type != "Arbiter":
                    if brick.size_used >= effective_capacity_used:
                        effective_capacity_used = brick.size_used

                    if effective_capacity_total == 0 or \
                      (brick.size_total <= effective_capacity_total and
                       brick.size_total > 0):
                        effective_capacity_total = brick.size_total

                    if brick.inodes_used >= effective_inodes_used:
                        effective_inodes_used = brick.inodes_used

                    if effective_inodes_total == 0 or \
                      (brick.inodes_total <= effective_inodes_total and
                       brick.inodes_total > 0):
                        effective_inodes_total = brick.inodes_total

            if subvol.type == TYPE_DISPERSE:
                # Subvol Size = Sum of size of Data bricks
                effective_capacity_used = effective_capacity_used * (
                    subvol.disperse_count - subvol.disperse_redundancy_count)
                effective_capacity_total = effective_capacity_total * (
                    subvol.disperse_count - subvol.disperse_redundancy_count)
                effective_inodes_used = effective_inodes_used * (
                    subvol.disperse_count - subvol.disperse_redundancy_count)
                effective_inodes_total = effective_inodes_total * (
                    subvol.disperse_count - subvol.disperse_redundancy_count)

            vol.size_total += effective_capacity_total
            vol.size_used += effective_capacity_used
            vol.size_free = vol.size_total - vol.size_used
            vol.inodes_total += effective_inodes_total
            vol.inodes_used += effective_inodes_used
            vol.inodes_free = vol.inodes_total - vol.inodes_used


def _parse_a_vol(volume_el):
    volume = VolumeInfo()
    volume.name = volume_el.find('name').text
    volume.id = volume_el.find('id').text
    volume.type = volume_el.find('typeStr').text
    volume.state = volume_el.find('statusStr').text
    volume.bricks_count = int(volume_el.find('brickCount').text)
    volume.distribute_count = int(volume_el.find('distCount').text)
    volume.replica_count = int(volume_el.find('replicaCount').text)
    volume.disperse_count = int(volume_el.find('disperseCount').text)
    volume.disperse_redundancy_count = int(
        volume_el.find('redundancyCount').text
    )
    transport = volume_el.find('transport').text
    volume.snapshot_count = int(volume_el.find('snapshotCount').text)
    bricks = []

    if transport == '0':
        volume.transport = 'tcp'
    elif transport == '1':
        volume.transport = 'rdma'
    else:
        volume.transport = 'tcp,rdma'

    for brk in volume_el.findall('bricks/brick'):
        brick = BrickInfo()
        if brk.find("isArbiter").text == '1':
            brick.type = "Arbiter"

        brick.node.hostname, brick.path = brk.find("name").text.rsplit(":", 1)
        brick.node.id = brk.find("hostUuid").text

        bricks.append(brick)

    for opt in volume_el.findall('options/option'):
        option = OptionInfo()
        option.name = opt.find('name').text
        option.value = opt.find('value').text

        volume.options.append(option)

    return [volume, bricks]


def _group_subvols(volumes):
    out_volumes = []
    for vol, bricks in volumes:
        subvol_type = vol.type.split("_")[-1]
        subvol_bricks_count = 1

        if vol.replica_count > 1:
            subvol_bricks_count = vol.replica_count

        if vol.disperse_count > 0:
            subvol_bricks_count = vol.disperse_count

        number_of_subvols = int(len(bricks) / subvol_bricks_count)

        for sidx in range(number_of_subvols):
            subvol = SubvolInfo()
            subvol.name = "%s-%s-%s" % (vol.name, subvol_type.lower(), sidx)
            subvol.replica_count = vol.replica_count
            subvol.disperse_count = vol.disperse_count
            subvol.disperse_redundancy_count = vol.disperse_redundancy_count
            subvol.type = subvol_type

            for bidx in range(subvol_bricks_count):
                subvol.bricks.append(
                    bricks[sidx*subvol_bricks_count + bidx]
                )
            vol.subvols.append(subvol)

        out_volumes.append(vol)

    return out_volumes


def _parse_a_brick_status(brick_el):
    brick = BrickInfo()
    brick.node = NodeInfo()
    brick.node.id = brick_el.find('peerid').text
    brick.node.hostname = brick_el.find('hostname').text
    brick.path = brick_el.find('path').text
    brick.state = "Offline"
    if brick_el.find('status').text == "1":
        brick.state = "Online"
        brick.pid = int(brick_el.find('pid').text)
        brick.size_total = int(brick_el.find('sizeTotal').text)
        brick.size_free = int(brick_el.find('sizeFree').text)
        brick.inodes_total = int(brick_el.find('inodesTotal').text)
        brick.inodes_free = int(brick_el.find('inodesFree').text)
        brick.size_used = brick.size_total - brick.size_free
        brick.inodes_used = brick.inodes_total - brick.inodes_free
        brick.device = brick_el.find('device').text
        brick.block_size = int(brick_el.find('blockSize').text)
        brick.mnt_options = brick_el.find('mntOptions').text
        brick.fs_name = brick_el.find('fsName').text

        # ISSUE #14 glusterfs 3.6.5 does not have 'ports' key
        # in vol status detail xml output
        if brick_el.find('ports'):
            brick.ports.tcp = brick_el.find('ports').find("tcp").text
            brick.ports.rdma = brick_el.find('ports').find("rdma").text
        else:
            brick.ports.tcp = brick_el.find('port')

    return brick


def parsed_volume_info(info):
    tree = etree.fromstring(info)
    volumes = []
    for volume_el in tree.findall('volInfo/volumes/volume'):
        try:
            volumes.append(_parse_a_vol(volume_el))
        except (ParseError, AttributeError, ValueError) as err:
            raise CommandOutputParseError from err

    return _group_subvols(volumes)


def parsed_volume_status(data, volinfo):
    tree = etree.fromstring(data)
    bricks_data = []
    for brick_el in tree.findall('volStatus/volumes/volume/node'):
        try:
            bricks_data.append(_parse_a_brick_status(brick_el))
        except (ParseError, AttributeError, ValueError) as err:
            raise CommandOutputParseError from err

    tmp_brick_status = {}
    for brk in bricks_data:
        tmp_brick_status[brk.node.hostname + ":" + brk.path] = brk

    for vidx, vol in enumerate(volinfo):
        for idx, subvol in enumerate(vol.subvols):
            for bidx, brk in enumerate(subvol.bricks):
                brick_status_data = tmp_brick_status.get(
                    brk.node.hostname + ":" + brk.path, None
                )

                if brick_status_data is None:
                    continue

                bdata = brick_status_data
                bdata.type = brk.type
                volinfo[vidx].subvols[idx].bricks[bidx] = bdata

    _update_volume_utilization(volinfo)
    _update_volume_health(volinfo)
    return volinfo
