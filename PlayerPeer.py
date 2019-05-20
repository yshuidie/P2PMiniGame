from Peer import *


#-----------------------------
#  Define actual msgtype string
#-----------------------------
PEERNAME = "NAME"   # request a peer's canonical id
LISTPEERS = "LIST"
INSERTPEER = "JOIN"
PEERQUIT = "QUIT"

REPLY = "REPL"
ERROR = "ERRO"

# Assumption in this program:
#   peer id's in this application are just "host:port" strings


class PlayerPeer(Peer):
	"""
	A minigame player entity based on Peer class.

	Initialize router & handler
	"""
	def __init__(self, maxpeers, serverport, debug=False):
		Peer.__init__(self, maxpeers, serverport,debug=debug)

		self.addrouter(self.__router) 

		handlers = {LISTPEERS : self.__handle_listpeers,
					INSERTPEER : self.__handle_insertpeer,
					PEERNAME: self.__handle_peername,
					PEERQUIT: self.__handle_quit
				   }
		for mt in handlers:
			self.addhandler(mt, handlers[mt])


	def __router(self, peerid):
		"""
		peerid: destination
		decide which known peer msgs should be routed to, to reach(hopefully) the desired peer
		return: next-peer-id, host, port
		host, port: IP address of next-peer-id
		"""
		if peerid not in self.getpeerids():
			return (None, None, None)  #message can't be routed
		else:
			rt = [peerid]
			rt.extend(self.peers[peerid])
			return rt


 	# precondition: may be a good idea to hold the lock before going
	#			   into this function
	def buildpeers(self, host, port, hops=1):
		""" buildpeers(host, port, hops) 
		host, port: peer's address
		Attempt to build the local peer list up to the limit stored by
		self.maxpeers, using a simple depth-first search given an
		initial host and port as starting point. The depth of the
		search is limited by the hops parameter.
		"""
		if self.maxpeersreached() or not hops:
			return

		peerid = None

		self.__debug("Building peers from (%s,%s)" % (host,port))

		try:
			_, peerid = self.connectandsend(host, port, PEERNAME, '')[0]

			self.__debug("contacted " + peerid)
			resp = self.connectandsend(host, port, INSERTPEER, 
						'%s %s %d' % (self.myid, 
								  self.serverhost, 
								  self.serverport))[0]
			self.__debug(str(resp))
			if (resp[0] != REPLY) or (peerid in self.getpeerids()):
				return

			self.addpeer(peerid, host, port)

			# do recursive depth first search to add more peers
			resp = self.connectandsend(host, port, LISTPEERS, '',
						pid=peerid)
			if len(resp) > 1:
				resp.reverse()
				resp.pop()	# get rid of the first reply: REPL #ids
				while len(resp):
					nextpid,host,port = resp.pop()[1].split()
					if nextpid != self.myid:
						self.buildpeers(host, port, hops - 1)
		except:
			if self.debug:
				traceback.print_exc()
			self.removepeer(peerid)


	#-----------------------
	# Specific message handlers
	#-----------------------------
	def __handle_peername(self, peerconn, data):
		""" Handles the NAME message type. Message data is not used. """
		peerconn.senddata(REPLY, self.myid)

	def __handle_listpeers(self, peerconn, data):
		""" Handles the LISTPEERS message type. Message data is not used. """
		self.peerlock.acquire()
		try:
			self.__debug('Listing peers %d' % self.numberofpeers())
			peerconn.senddata(REPLY, '%d' % self.numberofpeers())
			for pid in self.getpeerids():
				host,port = self.getpeer(pid)
				peerconn.senddata(REPLY, '%s %s %d' % (pid, host, port))
		finally:
			self.peerlock.release()


	def __handle_insertpeer(self, peerconn, data):
		""" 
		Handles the INSERTPEER (join) message type. The message data
		should be a string of the form, "peerid  host  port", where peer-id
		is the canonical name of the peer that desires to be added to this
		peer's list of peers, host and port are the necessary data to connect
		to the peer.
		"""
		self.peerlock.acquire()
		try:
			try:
				peerid,host,port = data.split()

				if self.maxpeersreached():
					self.__debug('maxpeers %d reached: connection terminating' 
						  % self.maxpeers)
					peerconn.senddata(ERROR, 'Join: too many peers')
					return

				# peerid = '%s:%s' % (host,port)
				if peerid not in self.getpeerids() and peerid != self.myid:
					self.addpeer(peerid, host, port)
					self.__debug('added peer: %s' % peerid)
					peerconn.senddata(REPLY, 'Join: peer added: %s' % peerid)
				else:
					peerconn.senddata(ERROR, 'Join: peer already inserted %s'
							   % peerid)
			except:
				self.__debug('invalid insert %s: %s' % (str(peerconn), data))
				peerconn.senddata(ERROR, 'Join: incorrect arguments')
		finally:
			self.peerlock.release()



	def __handle_quit(self, peerconn, data):
		""" 
		Handles the QUIT message type. The message data should be in the
		format of a string, "peer-id", where peer-id is the canonical
		name of the peer that wishes to be unregistered from this
		peer's directory.
		"""
		self.peerlock.acquire()
		try:
			peerid = data.lstrip().rstrip()
			if peerid in self.getpeerids():
				msg = 'Quit: peer removed: %s' % peerid 
				self.__debug(msg)
				peerconn.senddata(REPLY, msg)
				self.removepeer(peerid)
			else:
				msg = 'Quit: peer not found: %s' % peerid 
				self.__debug(msg)
				peerconn.senddata(ERROR, msg)
		finally:
			self.peerlock.release()

	def __debug( self, msg ):
		if self.debug:
			btdebug( msg )