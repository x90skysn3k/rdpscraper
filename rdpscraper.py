#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, time, os
import tempfile
import re
import argparse
import xml.dom.minidom
from PIL import Image
from PIL import ImageEnhance
import pytesseract
from io import BytesIO
import pyscreenshot as ImageGrab
import getopt
from PyQt4 import QtCore, QtGui
from rdpy.protocol.rdp import rdp
from rdpy.ui.qt4 import RDPBitmapToQtImage
import rdpy.core.log as log
from rdpy.core.error import RDPSecurityNegoFail
from twisted.internet import task
import threading
import itertools


class colors:
    white = "\033[1;37m"
    normal = "\033[0;00m"
    red = "\033[1;31m"
    blue = "\033[1;34m"
    green = "\033[1;32m"
    lightblue = "\033[0;34m"

services = {}

banner = colors.red + r"""

   ▄████████ ████████▄     ▄███████▄        ▄████████  ▄████████    ▄████████    ▄████████    ▄███████▄    ▄████████    ▄████████ 
  ███    ███ ███   ▀███   ███    ███       ███    ███ ███    ███   ███    ███   ███    ███   ███    ███   ███    ███   ███    ███ 
  ███    ███ ███    ███   ███    ███       ███    █▀  ███    █▀    ███    ███   ███    ███   ███    ███   ███    █▀    ███    ███ 
 ▄███▄▄▄▄██▀ ███    ███   ███    ███       ███        ███         ▄███▄▄▄▄██▀   ███    ███   ███    ███  ▄███▄▄▄      ▄███▄▄▄▄██▀ 
▀▀███▀▀▀▀▀   ███    ███ ▀█████████▀      ▀███████████ ███        ▀▀███▀▀▀▀▀   ▀███████████ ▀█████████▀  ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   
▀███████████ ███    ███   ███                     ███ ███    █▄  ▀███████████   ███    ███   ███          ███    █▄  ▀███████████ 
  ███    ███ ███   ▄███   ███               ▄█    ███ ███    ███   ███    ███   ███    ███   ███          ███    ███   ███    ███ 
  ███    ███ ████████▀   ▄████▀           ▄████████▀  ████████▀    ███    ███   ███    █▀   ▄████▀        ██████████   ███    ███ 
  ███    ███                                                       ███    ███                                          ███    ███ 
"""+'\n' \
+ '\n rdpscraper.py v0.1'\
+ '\n Created by: Steven Laura/@steven1664 && Jacob Robles/@shellfail && Shane Young/@x90skysn3k\n' + colors.normal

def make_dic_gnmap():
    global services
    port = None
    with open(args.file, 'r') as nmap_file:
        for line in nmap_file:
            supported = ['ms-wbt-server']
            for name in supported:
                matches = re.compile(r'([0-9][0-9]*)/open/[a-z][a-z]*//' + name)
                try:
                    port =  matches.findall(line)[0]
                except:
                    continue
    
                ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)
                tmp_ports = matches.findall(line)
                for tmp_port in tmp_ports:
                        if name in services:
                            if tmp_port in services[name]:
                                services[name][tmp_port] += ip
                            else:
                                services[name][tmp_port] = ip
                        else:
                            services[name] = {tmp_port:ip}


def make_dic_xml():
    global loading
    global services
    doc = xml.dom.minidom.parse(args.file)
    supported = ['ms-wbt-server']
    for host in doc.getElementsByTagName("host"):
        try:
            address = host.getElementsByTagName("address")[0]
            ip = address.getAttribute("addr")
            eip = ip.encode("utf8")
            iplist = eip.split(',')
        except:
            # move to the next host
            continue
        try:
            status = host.getElementsByTagName("status")[0]
            state = status.getAttribute("state")
        except:
            state = ""
        try:
            ports = host.getElementsByTagName("ports")[0]
            ports = ports.getElementsByTagName("port")
        except:
            continue

        for port in ports:
            pn = port.getAttribute("portid")
            state_el = port.getElementsByTagName("state")[0]
            state = state_el.getAttribute("state")
            if state == "open":
                try:
                    service = port.getElementsByTagName("service")[0]
                    port_name = service.getAttribute("name")
                except:
                    service = ""
                    port_name = ""
                    product_descr = ""
                    product_ver = ""
                    product_extra = ""
                name = port_name.encode("utf-8")
                tmp_port = pn.encode("utf-8")
                if name in services:
                    if tmp_port in services[name]:
                        services[name][tmp_port] += iplist
                    else:   
                        services[name][tmp_port] = iplist
                else:
                    services[name] = {tmp_port:iplist}

def loading():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if loading == True:
            break
        sys.stdout.write('\rTaking Screenshots Please Wait: ' + c)
        sys.stdout.flush()
        time.sleep(0.01)

# set log level
log._LOG_LEVEL = log.Level.WARNING


class RDPScreenShotFactory(rdp.ClientFactory):
    """
    @summary: Factory for screenshot exemple
    """
    __INSTANCE__ = 0
    __STATE__ = []

    def __init__(self, reactor, app, width, height, path, timeout):
        """
        @param reactor: twisted reactor
        @param width: {integer} width of screen
        @param height: {integer} height of screen
        @param path: {str} path of output screenshot
        @param timeout: {float} close connection after timeout s without any updating
        """
        RDPScreenShotFactory.__INSTANCE__ += 1
        self._reactor = reactor
        self._app = app
        self._width = width
        self._height = height
        self._path = path
        self._timeout = timeout
        #NLA server can't be screenshooting
        self._security = rdp.SecurityLevel.RDP_LEVEL_SSL

    def clientConnectionLost(self, connector, reason):
        """
        @summary: Connection lost event
        @param connector: twisted connector use for rdp connection (use reconnect to restart connection)
        @param reason: str use to advertise reason of lost connection
        """
        if reason.type == RDPSecurityNegoFail and self._security != "rdp":
            log.info("due to RDPSecurityNegoFail try standard security layer")
            self._security = rdp.SecurityLevel.RDP_LEVEL_RDP
            connector.connect()
            return

        log.info("connection lost : %s" % reason)
        RDPScreenShotFactory.__STATE__.append((connector.host, connector.port, reason))
        RDPScreenShotFactory.__INSTANCE__ -= 1
        if(RDPScreenShotFactory.__INSTANCE__ == 0):
            self._reactor.stop()
            self._app.exit()

    def clientConnectionFailed(self, connector, reason):
        """
        @summary: Connection failed event
        @param connector: twisted connector use for rdp connection (use reconnect to restart connection)
        @param reason: str use to advertise reason of lost connection
        """
        log.info("connection failed : %s"%reason)
        RDPScreenShotFactory.__STATE__.append((connector.host, connector.port, reason))
        RDPScreenShotFactory.__INSTANCE__ -= 1
        if(RDPScreenShotFactory.__INSTANCE__ == 0):
            self._reactor.stop()
            self._app.exit()

    def buildObserver(self, controller, addr):
        """
        @summary: build ScreenShot observer
        @param controller: RDPClientController
        @param addr: address of target
        """
        class ScreenShotObserver(rdp.RDPClientObserver):
            """
            @summary: observer that connect, cache every image received and save at deconnection
            """
            def __init__(self, controller, width, height, path, timeout, reactor):
                """
                @param controller: {RDPClientController}
                @param width: {integer} width of screen
                @param height: {integer} height of screen
                @param path: {str} path of output screenshot
                @param timeout: {float} close connection after timeout s without any updating
                @param reactor: twisted reactor
                """
                rdp.RDPClientObserver.__init__(self, controller)
                self._buffer = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
                self._path = path
                self._timeout = timeout
                self._startTimeout = False
                self._reactor = reactor

            def onUpdate(self, destLeft, destTop, destRight, destBottom, width, height, bitsPerPixel, isCompress, data):
                """
                @summary: callback use when bitmap is received 
                """
                image = RDPBitmapToQtImage(width, height, bitsPerPixel, isCompress, data);
                with QtGui.QPainter(self._buffer) as qp:
                # draw image
                    qp.drawImage(destLeft, destTop, image, 0, 0, destRight - destLeft + 1, destBottom - destTop + 1)
                if not self._startTimeout:
                    self._startTimeout = False
                    self._reactor.callLater(self._timeout, self.checkUpdate)

            def onReady(self):
                """
                @summary: callback use when RDP stack is connected (just before received bitmap)
                """
                log.info("connected %s" % addr)

            def onSessionReady(self):
                """
                @summary: Windows session is ready
                @see: rdp.RDPClientObserver.onSessionReady
                """
                pass

            def onClose(self):
                """
                @summary: callback use when RDP stack is closed
                """
                log.info("save screenshot into %s" % self._path)
                self._buffer.save(self._path)

            def checkUpdate(self):
                self._controller.close();

        controller.setScreen(self._width, self._height);
        controller.setSecurityLevel(self._security)
        return ScreenShotObserver(controller, self._width, self._height, self._path, self._timeout, self._reactor)

def main(width, height, path, timeout):
    """
    @summary: main algorithm
    @param height: {integer} height of screenshot
    @param width: {integer} width of screenshot
    @param timeout: {float} in sec
    @param hosts: {list(str(ip[:port]))}
    @return: {list(tuple(ip, port, Failure instance)} list of connection state
    """
    #create application
    app = QtGui.QApplication(sys.argv)

    #add qt4 reactor
    import qt4reactor
    qt4reactor.install()

    from twisted.internet import reactor


    with open(fname, 'r') as f:
        for ips in f:
            if ':' in ips:
                ip, port = ips.split(':')
            
            print "\nTaking Screenshot for: " + ip
            reactor.connectTCP(ip, int(port), RDPScreenShotFactory(reactor, app, width, height, path + "%s.jpg" % ip, timeout))

        reactor.runReturn()
        app.exec_()
        return RDPScreenShotFactory.__STATE__
    f.close()




def parse_args():
    
    parser = argparse.ArgumentParser(description=\
 
    "Usage: python rdpscraper.py <OPTIONS> \n")

    menu_group = parser.add_argument_group(colors.lightblue + 'Menu Options' + colors.normal)
    
    menu_group.add_argument('-f', '--file', help="GNMAP or XML file to parse", required=True)
    
   
    args = parser.parse_args()
    
    return args

print(banner)

args = parse_args()


try:
    tmppath = tempfile.mkdtemp(prefix="rdpscraper-tmp")
except:
    sys.stderr.write("\nError while creating rdpscaper temp directory.")
    exit(4)

width = 3072
height = 1536
path = tmppath + "/"
timeout = 10.0
bitsPerPixel = 24
Loading = False

try:
    doc = xml.dom.minidom.parse(args.file)
    make_dic_xml()
except:
    make_dic_gnmap()
if services is None:
    sys.exit(0)

t = threading.Thread(target=loading)
t.start()

for service in services:
    for port in services[service]:
        fname = tmppath + "/" + service + '-' + port
        iplist = services[service][port]
        f = open(fname, 'w+')
        for ip in iplist:
            f.write(ip + ':' + port + '\n')
        f.close()

main(width, height, path, timeout)

outputpath = "rdpscraper-output/"
if not os.path.exists(outputpath):
    os.mkdir(outputpath)


loading = True

with open(fname, 'r') as fn:
    for fns in fn:
        ip, port = fns.split(':')

        if not os.path.exists(tmppath + "/" + ip +'.jpg'):
            print "\nScreenshot Unsuccessful for " + ip
            continue

        img = Image.open(tmppath + "/" + ip +'.jpg')
        print "\nip address: " + ip + "\n"
        regex = re.compile(r'^[a-zA-Z0-9](_(?!(\.|_))|\.(?!(_|\.))|[a-zA-Z0-9]){6,18}[a-zA-Z0-9]$')
        string = pytesseract.image_to_string(img)
        if '2012' in string:
            img = img.resize([int(2.4 * s) for s in img.size])
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(0.7)
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(0.9)       
            #color = ImageEnhance.Color(img)
            #img = color.enhance(0.)
            string = pytesseract.image_to_string(img)
            #    output = "test.txt"
            #    with open(output, 'w+') as f:
            #        for line in string:
            #            f.write('\n'.join(line))
            #            f.write('\n')
                #print "found"       
        else:
            img = img.resize([int(2.2 * s) for s in img.size])
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(0.2)
            color = ImageEnhance.Color(img)
            img = color.enhance(0)
            #bright = ImageEnhance.Brightness(img)
            #img = bright.enhance(0.5)
            #contrast = ImageEnhance.Contrast(img)
            #img = contrast.enhance(0.2)
            string = pytesseract.image_to_string(img)
                #output = "test.txt"
                #with open(output, 'w+') as f:
                #    for line in string:
                #        f.write('\n'.join(line))
                #        f.write('\n')
                #print "found"
        #print(pytesseract.image_to_string(img))
        #print "------------------------------------------------------------------------------------------------------------\n"
        output = pytesseract.image_to_string(img)
        print output
        f = open(outputpath + "output-" + ip + ".txt", 'w+')
        f.write(output + '\n')
    f.close()
