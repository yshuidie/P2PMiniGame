##http://cs.berry.edu/~nhamid/p2p/framework-python.html

class Peer:
"""
Main function for a peer in a P2P network
"""
    def __init__( self, maxpeers, serverport, myid=None, serverhost = None ):
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

		# initialize other variables
		self.debug = 0  
		self.peers = {}  # list (dictionary/hash table) of known peers
		self.shutdown = False  # used to stop the main loop
		self.handlers = {}
		self.router = None


    def makeserversocket( self, port, backlog=5 ):
    	"""
    	create socket and bind to port
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
		Handle new peer connection from clientsock
    	"""
		self.__debug( 'Connected ' + str(clientsock.getpeername()) )

		host, port = clientsock.getpeername()
		peerconn = BTPeerConnection( None, host, port, clientsock, debug=False )
		
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
				clientsock, clientaddr = s.accept()
				clientsock.settimeout(None)

				#handle the communication in a new thread
				t = threading.Thread( target = self.__handlepeer, 
						      args = [ clientsock ] )
				t.start()
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