#!/usr/bin/env python
"""
cdbus.py - DBus service for controlling CBus.
Copyright 2012 Michael Farrell <micolous+git@gmail.com>

This library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library.  If not, see <http://www.gnu.org/licenses/>.
"""

# from http://twistedmatrix.com/trac/attachment/ticket/1352/dbus-twisted.py
from twisted.internet import glib2reactor
glib2reactor.install()

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.python import log
from cbus.protocol.pciprotocol import PCIProtocol
import sys
import dbus
import dbus.service
import gobject
from dbus.mainloop.glib import DBusGMainLoop
from optparse import OptionParser

DBusGMainLoop(set_as_default=True)

DBUS_INTERFACE = 'au.id.micolous.cbus.CBusInterface'
DBUS_SERVICE = 'au.id.micolous.cbus.CBusService'
DBUS_PATH = '/'

class CBusProtocolHandler(PCIProtocol):
	cbus_api = None
	
	def on_confirmation(self, code, success):
		if not self.cbus_api: return
		print "confirmation %r %r" % (code, success)


class CBusBackendAPI(dbus.service.Object):	
	def __init__(self, bus, protocol, object_path=DBUS_PATH):
		self.pci = protocol
		self.pci.cbus_api = self
		dbus.service.Object.__init__(self, bus, object_path)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='y', out_signature='s')
	def lighting_group_on(self, group_addr):
		return self.pci.lighting_group_on(group_addr)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='y', out_signature='s')
	def lighting_group_off(self, group_addr):
		return self.pci.lighting_group_off(group_addr)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='ynd', out_signature='s')
	def lighting_group_ramp(self, group_addr, duration, level):
		return self.pci.lighting_group_ramp(group_addr, duration, level)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='yyy', out_signature='s')
	def recall(self, unit_addr, param_no, count):
		# TODO: implement return response
		return self.pci.recall(unit_addr, param_no, count)
	
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='yy', out_signature='s')
	def identify(self, unit_addr, attribute):
		# TODO: implement return response
		return self.pci.identify(unit_addr, attribute)
	
	

	

def boot_dbus(serial_mode, addr, daemonise, pid_file, session_bus=False):
	if session_bus:
		bus = dbus.SessionBus()
	else:
		bus = dbus.SystemBus()
	
	name = dbus.service.BusName(DBUS_SERVICE, bus=bus)
	
	protocol = CBusProtocolHandler()
	api = CBusBackendAPI(name, protocol)
	
	if serial_mode:
		SerialPort(protocol, addr, reactor, baudrate=9600)
	else:
		raise NotImplementedError, 'Not implemented yet'
	
	
	
	
	
	"""mainloop = gobject.MainLoop()
	
	if daemonise:
		assert pid_file, 'Running in daemon mode means pid_file must be specified.'
		from daemon import daemonize
		daemonize(pid_file)
	
	gobject.threads_init()
	context = mainloop.get_context()"""

def main_optparse():
	parser = OptionParser(usage='%prog')
	parser.add_option('-D', '--daemon', action='store_true', dest='daemon', default=False, help='Start as a daemon [default: %default]')
	parser.add_option('-P', '--pid', dest='pid_file', default='/var/run/cdbusd.pid', help='Location to write the PID file.  Only has effect in daemon mode.  [default: %default]')
	
	parser.add_option('-s', '--serial-pci', dest='serial_pci', default=None, help='Serial port where the PCI is located.  Either this or -t must be specified.')
	parser.add_option('-t', '--tcp-pci', dest='tcp_pci', default=None, help='IP address and TCP port where the PCI is located (CNI).  Either this or -s must be specified.')
	parser.add_option('-S', '--session-bus', action='store_true', dest='session_bus', default=False, help='Bind to the session bus instead of the system bus [default: %default]')
	
	parser.add_option('-l', '--log-file', dest='log', default=None, help='Destination to write logs [default: stdout]')
	
	option, args = parser.parse_args()
	
	if option.serial_pci and option.tcp_pci:
		parser.error('Both serial and TCP CBus PCI addresses were specified!  Use only one...')
	elif option.serial_pci:
		serial_mode = True
		addr = option.serial_pci
	elif option.tcp_pci:
		serial_mode = False
		addr = option.tcp_pci
	else:
		parser.error('No CBus PCI address was specified!  (See -s or -t option)')
		
	if option.log:
		log.startLogging(option.log)
	else:
		log.startLogging(sys.stdout)
	
	reactor.callWhenRunning(boot_dbus, serial_mode, addr, option.daemon, option.pid_file, option.session_bus)
	reactor.run()

		
if __name__ == '__main__':
	main_optparse()

