# coding: utf-8
import sys

from PlayerPeer import *


def main():
	if len(sys.argv) < 4:
		print "Syntax: %s server-port max-peers peer-ip:port" % sys.argv[0]
		sys.exit(-1)

	serverport = int(sys.argv[1])
	maxpeers = sys.argv[2]
	firstpeer = sys.argv[3]

	print 'Welcome to Rock–paper–scissors online!'
	#debug = raw_input('Do you want to turn on debug mode? (y/n)')
	#username = raw_input('Please tell us your name (for other players to see):')


	me = PlayerPeer(maxpeers,serverport,debug=True)
	print me.serverhost
	print me.debug

	host,port = firstpeer.split(':') #parse target peer


	#build peer network
	me.buildpeers(host, int(port), hops=2)
	#retry = 'y'
	#while len(me.peers) == 0 and retry == 'y':
	#	retry = raw_input('No other peers. Try connect again? (y/n)')
	#	me.buildpeers(host, int(port), hops=2)

	t = threading.Thread( target = me.mainloop, args = [] )
	t.start()
	  
	#me.startstabilizer( self.btpeer.checklivepeers, 3 )
#	self.btpeer.startstabilizer( self.onRefresh, 3 )
	#after( 3000, self.onTimer )

	

# setup and run app
if __name__=='__main__':
	main()