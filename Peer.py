##http://cs.berry.edu/~nhamid/p2p/framework-python.html

import socket
import threading
import time
import traceback
from PeerConnection import *

def btdebug( msg ):
	""" Prints a messsage to the screen with the name of the current thread """
	print "[%s] %s" % ( str(threading.currentThread().getName()), msg )


class Peer:
	"""
	Main function for a peer in a P2P network
	"""
	def __init__( self, maxpeers, serverport, myid=None, serverhost = None, debug = False ):
		# Grab basic node info
		self.maxpeers = int(maxpeers)
		self.serverport = int(serverport)


		if serverhost: 
			self.serverhost = serverhost  #peer's IP address
		else:  #get IP by attempting to connect to an Internet host like Google.
			self.__initserverhost() 


		if myid: 
			self.myid = myid
		else:  #The peer id will be composed of the host address and port number
			self.myid = '%s:%d' % (self.serverhost, self.serverport)

		self.peerlock = threading.Lock()  # ensure proper access to
								# peers list (maybe better to use
								# threading.RLock (reentrant))

		# initialize other variables
		self.debug = debug 
		self.peers = {}  # list (dictionary/hash table) of known peers
		self.shutdown = False  # used to stop the main loop
		self.handlers = {} # msgtype: function ( peerconn, msgdata)  
		self.router = None  #Routing function to decide the peer to send msg

   	#-------------------------------------------------------------------------
	# Main functionality
	#-------------------------------------------------------------------------
	def makeserversocket( self, port, backlog=5 ):
		"""
		Create socket and bind to port
		Called in mainloop
		"""
		#creates a socket that will communicate using the IPv4 (AF_INET) protocol with TCP (SOCK_STREAM)
		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM ) 
		#socket.SO_REUSEADDR: port number of the socket will be immediately reusable after the socket is closed
		s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 ) #SOL_SOCKET, 1??
		s.bind( ( '', port ) ) #bind to a port
		s.listen( backlog ) # backlog: number of incoming connections that can queue up
		return s

	def __handlepeer( self, clientsock ):
		"""
		Handle new peer connection recieved from clientsock
		Called in mainloop
		"""
		self.__debug( 'New child ' + str(threading.currentThread().getName()) )
		self.__debug( 'Connected ' + str(clientsock.getpeername()) )

		host, port = clientsock.getpeername()
		peerconn = PeerConnection( None, host, port, clientsock, debug=False )
		
		try:
			msgtype, msgdata = peerconn.recvdata() #Get some data
			if msgtype: msgtype = msgtype.upper()

			if msgtype not in self.handlers:  
				self.__debug( 'Not handled: %s: %s' % (msgtype, msgdata) )
			else:
				self.__debug( 'Handling peer msg: %s: %s' % (msgtype, msgdata) )
				self.handlers[ msgtype ]( peerconn, msgdata )
		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
		
		self.__debug( 'Disconnecting ' + str(clientsock.getpeername()) )
		peerconn.close()


	def mainloop(self):
		"""
		Accept connections continously
		"""
		s = self.makeserversocket( self.serverport ) #new socket to send/recieve data on the connection
		s.settimeout(2)  #why?
		self.__debug( 'Server started: %s (%s:%d)'
				  % ( self.myid, self.serverhost, self.serverport ) )

		while not self.shutdown: #listening when on
			try:
				self.__debug( 'Listening for connections...' )
				time.sleep(5)
				clientsock, clientaddr = s.accept()

				#clientsock.settimeout(None)

				#handle the communication in a new thread
				#t = threading.Thread( target = self.__handlepeer, 
				#			  args = [ clientsock ] )
				
				#t.start()
				
			except KeyboardInterrupt:  #ctrl+C
				print 'KeyboardInterrupt: stopping mainloop'
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue

		# end while loop
		self.__debug( 'Main loop exiting' )

		s.close()


	def sendtopeer( self, peerid, msgtype, msgdata, waitreply=True ):
		"""
		Use routing function to decide peer to send, and then send it
		"""
		if self.router:
			nextpid, host, port = self.router( peerid )
		if not self.router or not nextpid:  #no function or fail
			self.__debug( 'Unable to route %s to %s' % (msgtype, peerid) )
			return None
		return self.connectandsend( host, port, msgtype, msgdata, pid=nextpid,
						waitreply=waitreply )


	def connectandsend( self, host, port, msgtype, msgdata, pid=None, waitreply=True ):
		msgreply = []   # list of replies
		try:
			peerconn = PeerConnection( pid, host, port, debug=self.debug )
			peerconn.senddata( msgtype, msgdata )
			self.__debug( 'Sent %s: %s' % (pid, msgtype) )
			
			if waitreply:
				onereply = peerconn.recvdata()
				while (onereply != (None,None)):  #(msgtype,msgdata)
					msgreply.append( onereply )
					self.__debug( 'Got reply %s: %s' % ( pid, str(msgreply) ) )
					onereply = peerconn.recvdata()
				peerconn.close()
		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
		
		return msgreply

	def checklivepeers( self ):
		""" 
		Attempts to ping all currently known peers in order to ensure that
		they are still active. Removes any from the peer list that do
		not reply. This function can be used as a simple stabilizer.
		"""
		todelete = []
		for pid in self.peers:
			isconnected = False
			try:
				self.__debug( 'Check live %s' % pid )
				host,port = self.peers[pid]
				peerconn = PeerConnection( pid, host, port, debug=self.debug )
				peerconn.senddata( 'PING', '' )
				isconnected = True
			except:
				todelete.append( pid )
			if isconnected:
				peerconn.close()

		self.peerlock.acquire()
		try:
			for pid in todelete: 
				if pid in self.peers: del self.peers[pid]
		finally:
			self.peerlock.release()
			

	#-------------------------------------------------------------------------
	# Settings & Initializations
	#-------------------------------------------------------------------------
	def __initserverhost( self ):
		""" 
		Attempt to connect to an Internet host in order to determine the
		local machine's IP address.
		Called by init if self.serverhost is not provided
		"""
		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		s.connect( ( "www.google.com", 80 ) )
		self.serverhost = s.getsockname()[0]
		s.close()


	def __debug( self, msg ):
		if self.debug:
			btdebug( msg )


	def setmyid( self, myid ):
		self.myid = myid


	def addrouter( self, router ):
		"""
		router(peername): Routing function that:
		Given a destination peername(not necessarily in self.peers),
		decide which known peer msgs should be routed to, to reach(hopefully) the desired peer
		return: next-peer-id, host, port
		host, port: IP address of next-peer-id
		next-peer-id = None if message can't be routed
		"""
		self.router = router	

	def addhandler( self, msgtype, handler ):
		""" Registers the handler for the given message type with this peer """
		assert len(msgtype) == 4
		self.handlers[ msgtype ] = handler


	def addpeer( self, peerid, host, port ):
		""" 
		Adds a peer name and host:port mapping to the known list of peers.
		"""
		if peerid not in self.peers and (self.maxpeers == 0 or len(self.peers) < self.maxpeers):
			self.peers[ peerid ] = (host, int(port))
			return True
		else:
			return False

	def getpeer( self, peerid ):
		""" Returns the (host, port) tuple for the given peer name """
		assert peerid in self.peers	# maybe make this just a return NULL?
		return self.peers[ peerid ]


	def removepeer( self, peerid ):
		""" Removes peer information from the known list of peers. """
		if peerid in self.peers:
			del self.peers[ peerid ]

   
	def addpeerat( self, loc, peerid, host, port ):
		""" 
		Inserts a peer's information at a specific position in the 
		list of peers. The functions addpeerat, getpeerat, and removepeerat
		should not be used concurrently with addpeer, getpeer, and/or 
		removepeer. 
		"""
		self.peers[ loc ] = (peerid, host, int(port))


	def getpeerat( self, loc ):
		if loc not in self.peers:
			return None
		return self.peers[ loc ]


	def removepeerat( self, loc ):
		removepeer( self, loc ) 

	def maxpeersreached( self ):
		""" 
		Returns whether the maximum limit of names has been added to the
		list of known peers. Always returns True if maxpeers is set to
		0.
		"""
		assert self.maxpeers == 0 or len(self.peers) <= self.maxpeers
		return self.maxpeers > 0 and len(self.peers) == self.maxpeers

	def getpeerids( self ):
		""" Return a list of all known peer id's. """
		return self.peers.keys()


	def numberofpeers( self ):
		""" Return the number of known peer's. """
		return len(self.peers)

	#-------------------------------------------------------------------------
	# Stabilizer function
	#-------------------------------------------------------------------------
	def __runstabilizer( self, stabilizer, delay ):
		while not self.shutdown:
			stabilizer()
			time.sleep( delay )

	def startstabilizer( self, stabilizer, delay ):
		""" 
		Registers and starts a stabilizer function with this peer. 
		The function will be activated every <delay> seconds. 
		"""
		t = threading.Thread( target = self.__runstabilizer, 
					  args = [ stabilizer, delay ] )
		t.start()










