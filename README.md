P2PMiniGame

Course Project: https://www.nyu.edu/classes/jcf/CSCI-GA.2440-001_sp18/

A simple P2P network that enable users to find a peer to play mini games.
One game Rock-Paper-Scissors is built.


Basic framework:
http://cs.berry.edu/~nhamid/p2p/framework-python.html

---------------------------------------------------------------------------
Run Method

In terminal with a Python 2 environment, type:

python R-P-S.py [your port] maxpeer [first peer IP]:[first peer port] 0
-The last parameter 0 stands for turning debug mode off.
-maxpeer = 0 stands for infinite peers.


Example: 
Open two local terminals and run the following command in each terminal:

python R-P-S.py 8889 0 localhost:8890 0
python R-P-S.py 8890 0 localhost:8889 0
