# coding: utf-8

from PlayerPeer import *
from Tkinter import *
games = {'1':'Rock–paper–scissors'}
RPS_hands = {'0':'Rock','1':'Paper','2':'Scissors'}


class GameClient():
	def __init__( self, firstpeer, hops=2, maxpeers=5, serverport=5678, master=None, debug = False):
		#-------------------------------------------------------------------------
		# Main procedure
		#-------------------------------------------------------------------------
		#Frame.__init__( self, master )
		self.me = PlayerPeer( maxpeers, serverport, debug=debug)
		host,port = firstpeer.split(':') #parse target peer

		#Join peer network & expand peer list
		self.me.buildpeers(host, int(port), hops=hops)  #if no other peers, this does nothing
		#Start listening to connections
		t = threading.Thread( target = self.me.main_loop, args = [] )
		t.daemon=True
		t.start()
		
		# keep update of peers
		self.me.startstabilizer( self.me.checklivepeers, 1000 )
	#	self.btpeer.startstabilizer( self.onRefresh, 3 )
		#self.after( 3000, self.onTimer )

	def choose_game(self):
		print 'Game Menu'
		for key,value in games.iteritems():
			print key,':', value
    
		self.gamechoice = raw_input('Please choose the game you want to play (or 0 to quit):')
		while self.gamechoice not in games.keys() and self.gamechoice != '0':
			self.gamechoice = raw_input('Invalid Input. Please choose the game you want to play:')
		if self.gamechoice == '0':
			print 'Bye!'
			self.me.shutdown = True
			sys.exit(0)

	def round(self, roundn):
		"""
		Actual game process of one round
		"""
		print "Round", roundn
		msg = raw_input('Say something to your opponent (Ex: I am going Scissor):')

		#Players send words to each other
		self.me.send_dialog(msg)

		#To do: improve the prompt once succeed
		while not self.me.opponentDialog:
			print "Waiting for opponent's words..."
			time.sleep(2)

		if self.me.opponentDialog:
			print "Opponent says:", self.me.opponentDialog
			self.me.opponentDialog = None #clear dialog for next use

		#Show hand to each other
		myhand = raw_input("Now show your hand (0 = Rock, 1 = Paper, 2 = Scissor): ")
		while myhand not in ['0','1','2']:
			myhand = raw_input("Invalid input, please try again (0 = Rock, 1 = Paper, 2 = Scissor):")

		self.me.send_hand(myhand)

		#To do: improve the prompt once succeed
		while not self.me.opponentHand:
			print "Waiting for opponent's hand..."
			time.sleep(2)

		if self.me.opponentHand:
			print "Opponent show hand: %s!" % RPS_hands[self.me.opponentHand]
			self.me.opponentHand = None #clear dialog for next use





	def main_loop(self):
		print 'Welcome to Rock–paper–scissors online!'

		time.sleep(2)  #wait for a while to build peer
		print 'Number of peers online: %d' % self.me.numberofpeers()
		#self.username = raw_input('Please tell us your name (for other players to see):')

		while self.me.status != Status.playing:	
			time.sleep(0.5)
			##Choose game
			self.choose_game()  #includes exit option
	#
			##Find a peer id
			self.me.status = Status.pairing
			self.me.pairing()
#
			if self.me.status == Status.playing:
				print "Game Start!"
				time.sleep(0.5)
				for i in range(1): #3 rounds
					self.round(i)

def main():
	if len(sys.argv) < 5:
		print "Syntax: %s server-port max-peers peer-ip:port debug" % sys.argv[0]
		sys.exit(-1)

	serverport = int(sys.argv[1])
	maxpeers = sys.argv[2]
	firstpeer = sys.argv[3]
	debug = False
	debug = int(sys.argv[4])

	
	client = GameClient(firstpeer=firstpeer, maxpeers=maxpeers, serverport=serverport,debug=debug)
	#while True:
	#	time.sleep(100)

	client.main_loop()
	#me.startstabilizer( self.btpeer.checklivepeers, 3 )
#	self.btpeer.startstabilizer( self.onRefresh, 3 )
	#after( 3000, self.onTimer )

	

# setup and run app
if __name__=='__main__':
	main()