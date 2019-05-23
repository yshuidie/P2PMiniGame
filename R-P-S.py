# coding: utf-8

from PlayerPeer import *
from Tkinter import *
games = {'1':'Rock–paper–scissors'}
RPS_hands = {'0':'Rock','1':'Paper','2':'Scissors'}
win = {'0':'2','1':'0','2':'1'}  #win situation: myhand:opponentHand
NWIN = 2  #Player who win 2 rounds first win the game.


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
		print '---------------------------------'
		print '||          Game Menu          ||'
		print '||0: Quit                      ||'
		for key,value in games.iteritems():
			print "||{0}: {1:30}||".format(key, value)
		print '---------------------------------'
    
		self.gamechoice = raw_input('Please choose the game you want to play:')
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
		##TODO: Bug: when nothing input but enter, opponent won't recieve message
		if msg == '' or msg == None or msg == '\n':
			msg == ' '
		self.me.send_dialog(msg)

		#To do: improve the prompt once succeed
		while not self.me.opponentDialog:
			print "Waiting for opponent's words..."
			time.sleep(2)

		if self.me.opponentDialog:
			print "Opponent says:", self.me.opponentDialog
			
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

		#Result
		if myhand == self.me.opponentHand: #draw case
			print "Draw!"
		elif win[myhand] == self.me.opponentHand: #win case
			self.me.win = self.me.win + 1
			print "You win by showing %s to %s! " % (RPS_hands[myhand],RPS_hands[self.me.opponentHand])
		else: #lose case
			self.me.lose = self.me.lose + 1
			print "You lose by showing %s to %s..." % (RPS_hands[myhand],RPS_hands[self.me.opponentHand])

		if self.me.win != NWIN and self.me.lose != NWIN:
			print "Score: %d:%d" % (self.me.win, self.me.lose)

		#clear data only used in this round
		self.me.opponentHand = None 
		self.me.opponentDialog = None 

	def main_loop(self):
		print 'Welcome to Leisure game platform online!'

		time.sleep(2)  #wait for a while to build peer
		print 'Number of peers online: %d' % self.me.numberofpeers()
		#self.username = raw_input('Please tell us your name (for other players to see):')

		while self.me.status == Status.idle:	
			time.sleep(0.5)
			##Choose game
			self.choose_game()  #includes exit option
	#
			##Find a peer id
			self.me.status = Status.pairing
			self.me.pairing()
#
			if self.me.status == Status.playing:
				print "Game Start! The player who win %d rounds wins!" % NWIN
				time.sleep(0.5)

				rCount = 1
				while True:  
					self.round(rCount)
					if self.me.win == NWIN:
						print "Congrats! You win this game by %d:%d" % (self.me.win, self.me.lose)
						break
					elif self.me.lose == NWIN:
						print "You lose the game by %d:%d...But you will win next time!" % (self.me.win, self.me.lose)
						break						
					rCount = rCount + 1

			#Game ends, reset data only used in this game
			self.me.status = Status.idle
			self.me.win = 0
			self.me.lose = 0


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