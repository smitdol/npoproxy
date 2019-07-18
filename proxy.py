#!/usr/bin/python
#based on http://voorloopnul.com/blog/a-python-proxy-in-less-than-100-lines-of-code/
import socket
import select
import time
import sys
from array import array

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 2048
delay = 0.0001

def dbgprint(s):
    print s
    sys.stdout.flush()

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port, request):
        try:
            self.forward.connect((host, port))
            self.forward.send(request);
            return self.forward
        except Exception, e:
            print e
            return False

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)
        self.host = 'ipv4.api.nos.nl'
        self.location = ''
        self.contentlength = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        self.proxy_ip_port=IP+':'+str(port)
    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                self.serverdata = self.s.recv(buffer_size)
                if len(self.serverdata) > 0:
                    self.on_recv()
                else:
                    self.on_close()
                    break
    def on_accept(self):
        clientsock, clientaddr = self.server.accept()
        data=clientsock.recv(buffer_size)
        dbgprint('>clientdata>'+data)

        lines = data.splitlines()
        for line in lines:
                pos = line.find('&h057=')
                if (pos != -1):
                     self.host = line[pos+len('&h057='):].split(' ')[0]  #host
        data=data.replace(self.proxy_ip_port,self.host)
        data=data.replace('&h057='+self.host,'')
        data=data.replace('&amp;h057='+self.host,'')
        dbgprint('>modclientdata>'+data)
        dbgprint('self.host:'+self.host)
        self.referer=self.host+data.splitlines()[0].split()[1]
        dbgprint('self.referer:'+self.referer)

        forward = Forward().start(self.host, 80, data)
        if forward:
            print clientaddr, "has connected" 
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            dbgprint("Can't establish connection with remote server.",)
            dbgprint("Closing connection with client side", clientaddr)
            clientsock.close()

    def on_close(self):
        dbgprint("on_close")
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.serverdata
        dbgprint('<recv<'+data)
        lines = data.splitlines()
        loc = ''
        variants = []
        streams = []
        avgbwds = []
        newVariant = False
        modlocation = ''
        for line in lines:
            if line.lower().startswith('location: '):
                # get location from line: split on space and get second element
                self.location = line.split()[1]
                # split host and request http://host/request
                tmp = self.location.split('/')
                self.host = tmp[2] 
                modlocation = self.location.replace(self.host,self.proxy_ip_port)
                if ('?' in modlocation):
                    loc = modlocation+'&h057='+self.host
                else:
                    loc = modlocation+'?h057='+self.host
            if newVariant:
                dbgprint('stream: '+line)
                streams.append(line)
                newVariant = False
            if line.upper().startswith('#EXT-X-STREAM-INF:') and 'RESOLUTION' in line:
                dbgprint('variant: '+line)
                variants.append(line)
                newVariant = True #next line is stream
            if line.startswith('Content-Length:'):
                self.contentlength = int(line.split()[1])
                dbgprint('contentlength: '+line.split()[1])
        if len(variants) == 0:
            data=data.replace(self.host,self.proxy_ip_port)
            data=data.replace(modlocation, loc)
            modlocation = modlocation.replace('&','&amp;')
            loc = loc.replace('&','&amp;')
            data=data.replace(modlocation, loc)
        else:
            target = 0
            for variant in variants:
                tmp=variant.split(':')[1]
                namevaluepairs=tmp.split(',')
                for key in namevaluepairs:
                    if key.startswith('AVERAGE-BANDWIDTH=') or key.startswith('BANDWIDTH='):
                        avgbwd = int(key.split('=')[1])
                        if avgbwd < 1999000 and avgbwd > target:
                            target = avgbwd
            #remove other streams from data
            modlines = []
            index = 0
            skiplines = 0
            for line in lines:
                if skiplines > 0 :
                    skiplines = skiplines - 1
                    index = index + 1
                    continue
                if line.upper().startswith('#EXT-X-STREAM-INF:'):
                    index = index + 1
                    if str(target) in line:
                        modlines.append(line)
                        if (self.location==''):
                            pos=self.referer.rfind('/')+1
                            modlines.append('http://'+self.referer[0:pos]+lines[index]) # add full path
                            skiplines = 1
                        else:
                            pos=self.location.rfind('/')+1
                            modlines.append(self.location[0:pos]+lines[index]) # add full path
                            skiplines = 1
                        continue
                    else:
                        skiplines = 1 #skip this line (i.e. do not append) and skip next line
                        continue
                modlines.append(line)
                index = index + 1
            data='\n'.join(modlines)
            datalength = len(data)
            while datalength <= self.contentlength:
                data = data + ' '
                datalength = datalength + 1
        dbgprint('<modified received data to client<\n'+data)
        if 'BANDWIDTH=' in data:
            self.host = 'ipv4.api.nos.nl'
            self.location = ''
            self.contentlength = 0
        self.channel[self.s].send(data)

if __name__ == '__main__':
    while 1:
        server = TheServer('', 9090)
        try:
            server.main_loop()
        except KeyboardInterrupt:
            print "Ctrl C - Stopping server"
            sys.exit(1)
        except socket.error as e:
            print "SocketError "+e.errno

