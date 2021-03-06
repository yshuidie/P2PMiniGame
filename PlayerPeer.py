import enum
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

STATUS = "STAT"  #request a peer's status
DIALOG = "DIAL"  #send a sentence
HAND = "HAND" #send 

#-----------------------------
#  Define player status
#-----------------------------
class Status(enum.Enum):
	idle = 0
	pairing = 1
	playing = 2


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

		handlers = {LISTPEERS: self.__handle_listpeers,
					INSERTPEER : self.__handle_insertpeer,
					PEERNAME: self.__handle_peername,
					PEERQUIT: self.__handle_quit,
					STATUS: self.__handle_status,
					DIALOG: self.__handle_dialog,
					HAND: self.__handle_hand,
				   }
		for mt in handlers:
			self.addhandler(mt, handlers[mt])

		self.status = Status.idle
		self.peerid = None #the pairing player
		self.opponentDialog = None #dialog from self.peerid (opponent)
		self.opponentHand = None #hand of self.peerid (opponent)
		self.win = 0  #number of rounds the player win in a game
		self.lose = 0 #number of rounds the player lose in a game

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


	def pairing(self):
		"""
		Find a peer who is pairing for game
		"""
		cont = 'y'
		while cont == 'y' and self.status == Status.pairing: 
			todelete = []
			for pid in self.peers:
				try:
					self.__debug( 'Requesting status of %s' % pid )
					host,port = self.peers[pid]
					resp = self.sendtopeer(pid, STATUS, self.myid)  #!#ask peer for status
					pstatus = resp.pop()[1]
					if pstatus == str(Status.pairing):
						print 'Found player: %s' % pid
						self.status = Status.playing
						self.peerid = pid
						return
				except:
					if self.debug:
						traceback.print_exc()
			
			cont = None
			while self.status == Status.pairing and cont != 'y' and cont != 'n':
				cont = raw_input('Can\'t find another peer pairing. Try again? (y/n)')

				if cont == 'n':
					self.shutdown = True
					self.status == Status.idle

		
	def send_dialog(self,msg):
		"""
		Send msg to self.peerid. 
		msg: some string.
		Todo: repeat if fails
			string length limit?
		"""
		self.__debug("Sending message [%s] to %s" % (msg,self.peerid))
		try:
			resp = self.sendtopeer(self.peerid, DIALOG, msg)[0]
			self.__debug(str(resp))
		except:
			print "Failed to send message to peer. Trying again..."


	def send_hand(self,hand):
		"""
		Send hand to self.peerid
		hand: '0','1', or '2'
		Todo: repeat if fails
		"""
		self.__debug("Sending hand [%s] to %s" % (hand, self.peerid))
		try:
			resp = self.sendtopeer(self.peerid, HAND, hand)[0]
			self.__debug(str(resp))
		except:
			print "Failed to send hand to peer. Trying again..."

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


	def __handle_status(self, peerconn, data):
		""" 
		Handles the STAT message type. Message data is the id of the sender. 
		If Node is pairing, change its status to playing
		"""
		self.peerlock.acquire()
		try:
			msg = 'Sending back status: %s' % self.status
			self.__debug(msg)
			peerconn.senddata(REPLY, str(self.status))
			if self.status == Status.pairing:
				self.peerid = data.lstrip().rstrip()
				print '\nFound player: %s. Press enter to continue.' % self.peerid
				self.status = Status.playing
		except:
			self.__debug('Failed to send status')
		finally:
			self.peerlock.release()

	def __handle_dialog(self, peerconn, data):
		""" 
		Handles the DIAL message type. Message data is the opponent's words. 
		"""
		self.peerlock.acquire()
		try:
			self.opponentDialog = data.lstrip().rstrip()
			self.__debug('Opponent dialog added: [%s]' % self.opponentDialog)
			peerconn.senddata(REPLY, 'DIAL: Dialog recieved')
		except:
			self.__debug('Failed to send reply')
		finally:
			self.peerlock.release()

	def __handle_hand(self, peerconn, data):
		""" 
		Handles the HAND message type. Message data is the opponent's hand. 
		"""
		self.peerlock.acquire()
		try:
			self.opponentHand = data.lstrip().rstrip()
			self.__debug('Opponent hand added: [%s]' % self.opponentHand)
			peerconn.senddata(REPLY, 'HAND: Hand recieved')
		except:
			self.__debug('Failed to send reply')
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