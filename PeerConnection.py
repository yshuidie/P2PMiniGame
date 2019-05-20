import socket
import struct
import threading
import time
import traceback


class PeerConnection:
    def __init__( self, peerid, host, port, sock=None, debug=False ):
	# any exceptions thrown upwards
		self.id = peerid
		self.debug = debug

		if not sock:  #If client socket hasn't been created
		    self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		    self.socket.connect( ( host, int(port) ) )
		else:
		    self.socket = sock

		#create a local file that saves message to sent temporarily
		self.buffer = self.socket.makefile( 'rw', 0 )  


    def __makemsg( self, msgtype, msgdata ):
		msglen = len(msgdata)
		msg = struct.pack( "!4sL%ds" % msglen, msgtype, msglen, msgdata )
		return msg


    def senddata( self, msgtype, msgdata ):
		"""
		senddata( message type, message data ) -> boolean status

		Send a message through a peer connection. Returns True on success
		or False if there was an error.
		"""
		try:
		    msg = self.__makemsg( msgtype, msgdata )
		    self.buffer.write( msg )
		    self.buffer.flush()  #send
		except KeyboardInterrupt:
		    raise
		except:
		    if self.debug:
			traceback.print_exc()
		    return False
		return True
	    
    def recvdata( self ):
		"""
		recvdata() -> (msgtype, msgdata)

		Receive a message from a peer connection. Returns (None, None)
		if there was any error.
		"""
		try:
		    msgtype = self.buffer.read( 4 )
		    if not msgtype: return (None, None)
		    
	        lenstr = self.buffer.read( 4 )
		    msglen = int(struct.unpack( "!L", lenstr )[0])  
		    msg = ""

		    #read until there's message
		    while len(msg) != msglen:  
				data = self.buffer.read( min(2048, msglen - len(msg)) )
				if not len(data):
				    break
				msg += data

		    if len(msg) != msglen:
				return (None, None)

		except KeyboardInterrupt:
		    raise
		except:
		    if self.debug:
				traceback.print_exc()
		    return (None, None)
		return ( msgtype, msg )

    def close( self ):
		"""
		Close the peer connection. The send and recv methods will not work
		after this call.
		"""
		self.socket.close()
		self.socket = None
		self.buffer = None


    def __str__( self ):
		return "|%s|" % peerid

    def __debug( self, msg ):
		if self.debug:
		    btdebug( msg )
