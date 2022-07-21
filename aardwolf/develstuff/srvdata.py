from aardwolf.protocol.T124.GCCPDU import GCCPDU
from aardwolf.protocol.T124.userdata import TS_UD, TS_SC
from aardwolf.protocol.T124.userdata.constants import *
from aardwolf.protocol.T124.userdata.clientcoredata import TS_UD_CS_CORE
from aardwolf.protocol.T124.userdata.clientsecuritydata import TS_UD_CS_SEC
from aardwolf.protocol.T124.userdata.clientnetworkdata import TS_UD_CS_NET, CHANNEL_DEF
from aardwolf.protocol.T124.userdata.clientclusterdata import TS_UD_CS_CLUSTER
from aardwolf.protocol.T128.security import TS_SECURITY_HEADER,SEC_HDR_FLAG
from aardwolf.protocol.T125.infopacket import *
from aardwolf.protocol.T125.extendedinfopacket import *
from aardwolf.protocol.T125.MCSPDU_ver_2 import MCSPDU_ver_2
from aardwolf.protocol.T128.serverdemandactivepdu import *
from aardwolf.protocol.T128.clientconfirmactivepdu import *
from aardwolf.protocol.T128.synchronizepdu import *
from aardwolf.protocol.T128.controlpdu import *
from aardwolf.protocol.T128.fontlistpdu import *
from aardwolf.protocol.T128.inputeventpdu import *
import asn1tools



if __name__ == '__main__':
	t125_ber_codec = asn1tools.compile_string(MCSPDU_ver_2, 'ber')
	t125_per_codec = asn1tools.compile_string(MCSPDU_ver_2, 'per')
	t124_codec = asn1tools.compile_string(GCCPDU, 'per')


	server_res_raw = bytes.fromhex('7f668201450a0100020100301a020122020103020100020101020100020101020300fff80201020482011f000500147c00012a14760a01010001c0004d63446e8108010c080004000800030c1400eb030500ec03ed03ee03ef03f0030000020cec00020000000200000020000000b8000000dadc9415801c24b7843e73e28d8a8c7a28455f25ec31e95f712af97475fba4fc01000000010000000100000006005c005253413148000000000200003f000000010001004104e24db384f3b472cf2a11d4ce00ae14412fadac2d2e015575f9cbe3d94e07f5aa2f0630b39b4970ff81cbc3166f4b9cf4bd9dd958ab942ee0b049a472c69d000000000000000008004800a90fae4fdfe89cb25c49b848888beae402d4b709aee52bc197eeca653c27a2527ef3773f59e5f106cd4c0c427068fdb5e880ea275bfbbcf74c204291f834a9490000000000000000')
	server_res_t125 = t125_ber_codec.decode('ConnectMCSPDU', server_res_raw)
	#print(server_res_t125)
	if server_res_t125[0] != 'connect-response':
		raise Exception('Unexpected response! %s' % server_res_t125)
	if server_res_t125[1]['result'] != 'rt-successful':
		raise Exception('Server returned error! %s' % server_res_t125)
	
	server_res_t124 = t124_codec.decode('ConnectData', server_res_t125[1]['userData'])
	if server_res_t124['t124Identifier'][1] != '0.0.20.124.0.1':
		raise Exception('Unexpected T124 response: %s' % server_res_t124)
	data = server_res_t124['connectPDU']
	m = server_res_raw.find(data)
	remdata = server_res_raw[m+len(data):]
	server_connect_pdu_raw = t124_codec.decode('ConnectGCCPDU', server_res_t124['connectPDU']+remdata)
	server_connect_pdu = TS_SC.from_bytes(server_connect_pdu_raw[1]['userData'][0]['value']).serverdata
