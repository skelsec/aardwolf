from aardwolf.protocol.tpkt import TPKT
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm




if __name__ == '__main__':
	reqdata = bytes.fromhex('0300002b26e00000000000436f6f6b69653a206d737473686173683d646576656c0d0a0100080003000000')
	tpkt = TPKT.from_bytes(reqdata)
	print(tpkt)
	conreq = ConnectionRequest.from_bytes(tpkt.tpdu)
	print(conreq)
	x = conreq.to_bytes()
	print(tpkt.tpdu.hex())
	print(x.hex())

	print(tpkt.tpdu == x)

	respdata = bytes.fromhex('030000130ed00000123400021f080002000000')
	tpkt = TPKT.from_bytes(respdata)
	print(tpkt)
	connres = ConnectionConfirm.from_bytes(tpkt.tpdu)
	print(connres)
	x = connres.to_bytes()
	print(tpkt.tpdu.hex())
	print(x.hex())
	print(tpkt.tpdu == x)
