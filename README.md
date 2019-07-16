# npoproxy
proxy to select lower bitrates of npo streams so that you can watch these streams also with less performant hardware

usage: run proxy.py on dedicated hardware (e.g. raspberrypi)

set up stream on reciever to point to proxy

e.g. 

#SERVICE 4097:0:1:5225:C99:3:EB0000:0:0:0:http%3a//192.168.1.196%3a9090/resolve.php/livestream?url=/live/npo/tvlive/npo1/npo1.isml/.m3u8:NPO1 Stream

#DESCRIPTION NPO1 Stream

where proxy runs on 192.168.1.196:9090 (adapt this to your situation, also in proxy.py)

after some back-and-forth the reciever gets the url to the stream with a bitrate of less than 2 MB/s

# Advanced usage
#SERVICE 4097:0:1:0:0:0:0:0:0:0:http%3a//192.168.1.196%3a9090/rijnmondTv/index.m3u8&h057=d3r4bk4fg0k2xi.cloudfront.net:RTV Rijnmond

#DESCRIPTION RTV Rijnmond

where h057=d3r4bk4fg0k2xi.cloudfront.net indicates to the proxy the original host of the stream

streams can be found on github.com/haroo/HansSettings 
