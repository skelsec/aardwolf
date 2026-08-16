"""T.124 GCC userdata block round-trips."""

import pytest

from aardwolf.protocol.T124.userdata import TS_SC, TS_UD
from aardwolf.protocol.T124.userdata.clientclusterdata import TS_UD_CS_CLUSTER
from aardwolf.protocol.T124.userdata.clientcoredata import TS_UD_CS_CORE
from aardwolf.protocol.T124.userdata.clientmessagechanneldata import TS_UD_CS_MCS_MSGCHANNEL
from aardwolf.protocol.T124.userdata.clientnetworkdata import CHANNEL_DEF, TS_UD_CS_NET
from aardwolf.protocol.T124.userdata.clientsecuritydata import TS_UD_CS_SEC
from aardwolf.protocol.T124.userdata.constants import (
    COLOR_DEPTH,
    ENCRYPTION_FLAG,
    TS_UD_TYPE,
    ChannelOption,
    ClusterInfo,
)
from aardwolf.protocol.T124.userdata.servercoredata import TS_UD_SC_CORE
from aardwolf.protocol.T124.userdata.constants import RNS_UD_SC


pytestmark = pytest.mark.unit


def make_client_core():
    core = TS_UD_CS_CORE()
    core.desktopWidth = 1024
    core.desktopHeight = 768
    core.colorDepth = COLOR_DEPTH.COLOR_16BPP_565
    core.clientBuild = 2600
    core.clientName = "AARDWOLF"
    core.imeFileName = ""
    return core


def test_client_core_round_trip():
    core = make_client_core()
    parsed = TS_UD_CS_CORE.from_bytes(core.to_bytes())
    assert parsed.desktopWidth == 1024
    assert parsed.desktopHeight == 768
    assert parsed.colorDepth == COLOR_DEPTH.COLOR_16BPP_565
    assert parsed.clientName.rstrip("\x00") == "AARDWOLF"
    assert parsed.to_bytes() == core.to_bytes()


def test_client_security_round_trip():
    security = TS_UD_CS_SEC()
    security.encryptionMethods = ENCRYPTION_FLAG.BIT_128
    security.extEncryptionMethods = ENCRYPTION_FLAG.FRENCH
    parsed = TS_UD_CS_SEC.from_bytes(security.to_bytes())
    assert parsed.encryptionMethods == ENCRYPTION_FLAG.BIT_128
    assert parsed.to_bytes() == security.to_bytes()


def test_client_network_channel_array_round_trip():
    channel = CHANNEL_DEF()
    channel.name = "cliprdr"
    channel.options = ChannelOption.INITIALIZED | ChannelOption.ENCRYPT_RDP
    network = TS_UD_CS_NET()
    network.channelDefArray = [channel]
    parsed = TS_UD_CS_NET.from_bytes(network.to_bytes())
    assert parsed.channelCount == 1
    assert parsed.channelDefArray[0].name == "cliprdr"
    assert ChannelOption.INITIALIZED in parsed.channelDefArray[0].options
    assert parsed.to_bytes() == network.to_bytes()


def test_client_cluster_round_trip():
    cluster = TS_UD_CS_CLUSTER()
    cluster.Flags = ClusterInfo.REDIRECTION_SUPPORTED
    cluster.RedirectedSessionID = 0
    parsed = TS_UD_CS_CLUSTER.from_bytes(cluster.to_bytes())
    assert parsed.Flags == ClusterInfo.REDIRECTION_SUPPORTED
    assert parsed.RedirectedSessionID == 0
    assert parsed.to_bytes() == cluster.to_bytes()


def test_client_message_channel_round_trip():
    channel = TS_UD_CS_MCS_MSGCHANNEL()
    parsed = TS_UD_CS_MCS_MSGCHANNEL.from_bytes(channel.to_bytes())
    assert parsed.type == TS_UD_TYPE.CS_MCS_MSGCHANNEL
    assert parsed.to_bytes() == channel.to_bytes()


def test_ts_ud_container_round_trip():
    container = TS_UD()
    container.userdata[TS_UD_TYPE.CS_CORE] = make_client_core()
    security = TS_UD_CS_SEC()
    security.encryptionMethods = ENCRYPTION_FLAG.BIT_128
    security.extEncryptionMethods = ENCRYPTION_FLAG.FRENCH
    container.userdata[TS_UD_TYPE.CS_SECURITY] = security
    parsed = TS_UD.from_bytes(container.to_bytes())
    assert TS_UD_TYPE.CS_CORE in parsed.userdata
    assert TS_UD_TYPE.CS_SECURITY in parsed.userdata
    assert parsed.userdata[TS_UD_TYPE.CS_CORE].desktopWidth == 1024


def test_server_core_round_trip():
    core = TS_UD_SC_CORE()
    core.version = 0x00080004
    core.clientRequestedProtocols = 1
    core.earlyCapabilityFlags = RNS_UD_SC.DYNAMIC_DST_SUPPORTED
    parsed = TS_UD_SC_CORE.from_bytes(core.to_bytes())
    assert parsed.version == 0x00080004
    assert parsed.earlyCapabilityFlags == RNS_UD_SC.DYNAMIC_DST_SUPPORTED
    assert parsed.to_bytes() == core.to_bytes()


def test_ts_sc_container_round_trip():
    container = TS_SC()
    core = TS_UD_SC_CORE()
    core.version = 0x00080004
    core.clientRequestedProtocols = 0
    core.earlyCapabilityFlags = RNS_UD_SC(0)
    container.serverdata[TS_UD_TYPE.SC_CORE] = core
    parsed = TS_SC.from_bytes(container.to_bytes())
    assert TS_UD_TYPE.SC_CORE in parsed.serverdata
    assert parsed.serverdata[TS_UD_TYPE.SC_CORE].version == 0x00080004
