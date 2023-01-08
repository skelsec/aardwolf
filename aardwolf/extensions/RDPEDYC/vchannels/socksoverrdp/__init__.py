import io
import asyncio
from aardwolf.extensions.RDPEDYC.vchannels import VirtualChannelBase

# SOCKS over RDP vchannel
#
# This vchannel is compatible with the "SocksOverRDP" project written by Balazs Bucsay (@xoreipeip)
# 
# To make use of this, you'll need to log in to the server and execute the "SocksOverRDP-Server" component 
# from the following repo https://github.com/nccgroup/SocksOverRDP
# The server component doesn't require administrative privileges, however 
# it will only run until your session is alive. You'll have to re-launch it every time you log in.
#
# Thank you for the cool project Balazs!

class SOCKSDataMessage:
    def __init__(self, connid:int, iserror:bool, data:bytes):
        self.connid = connid
        self.datalen = len(data)
        self.iserror = iserror
        self.data = data

    def to_bytes(self):
        t = self.connid.to_bytes(4, byteorder='little', signed=False)
        t += self.datalen.to_bytes(4, byteorder='little', signed=False)
        t += bytes([int(self.iserror)])
        t += self.data
        return t

    @staticmethod
    def from_bytes(data:bytes):
        return SOCKSDataMessage.from_buffer(io.BytesIO(data))
    
    @staticmethod
    def from_buffer(buff:io.BytesIO):
        connid = int.from_bytes(buff.read(4), byteorder='little', signed=False)
        datalen = int.from_bytes(buff.read(4), byteorder='little', signed=False)
        iserror = bool(buff.read(1)[0])
        data = buff.read(datalen)
        return SOCKSDataMessage(connid, iserror, data)
    
    def __str__(self):
        t = ''
        for k in self.__dict__:
            t += '%s: %s\r\n' % (k, self.__dict__[k])
        return k

class SocksOverRDPChannel(VirtualChannelBase):
    def __init__(self, channelname, listen_ip:str, listen_port:int):
        VirtualChannelBase.__init__(self, channelname)
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.__server = None
        self.__connection_id = 1
        self.__connections = {}

    def get_connection_id(self):
        t = self.__connection_id
        self.__connection_id += 1
        return t

    async def __handle_tcp_client(self, reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        try:
            #print('Client connected!')
            connid = self.get_connection_id()
            self.__connections[connid] = writer
            while True:
                data = await reader.read(1590)
                if data == b'':
                    #print('Client disconnected!')
                    return
                msg = SOCKSDataMessage(connid, False, data)
                await self.channel_data_out(msg.to_bytes())

        except Exception as e:
            print('Error! %s' % e)
            return
        finally:
            msg = SOCKSDataMessage(connid, True, b'AAAA')
            await self.channel_data_out(msg.to_bytes())

    async def channel_init(self):
        #print('Channel init called!')
        self.__server = await asyncio.start_server(self.__handle_tcp_client, self.listen_ip, self.listen_port)
        print('SOCKS server listening on %s:%s' % (self.listen_ip, self.listen_port))
        return True, None

    async def channel_data_in(self, data:bytes):
        try:
            msg = SOCKSDataMessage.from_bytes(data)
            if msg.connid not in self.__connections:
                print('MSG recieved for unknown connid "%s"' % msg.connid)
                return
            if msg.iserror is False:
                self.__connections[msg.connid].write(msg.data)
                await self.__connections[msg.connid].drain()

            else:
                print('Remote end terminated the connection!')
                self.__connections[msg.connid].close()
                del self.__connections[msg.connid]
        except Exception as e:
            print('Error! %s' % e)
            return

    async def channel_closed(self):
        for connid in self.__connections:
            self.__connections[connid].close()
        self.__server.close()

