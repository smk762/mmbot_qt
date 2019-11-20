# mmbot_qt
MarketMaker2 BobBot GUI for pythonQT  

sudo apt-get install python3.6 python3-pip libgnutls28-dev python3-venv python3-dev libpython3-dev libevent-dev libssl-dev libcurl4-openssl-dev 
pip3 install setuptools wheel 
pip3 install PyQt5==5.9.2 fbs pyqtgraph   
pip3 install slick-bitcoinrpc python-bitcoinlib pycrypto   
pip3 install pyqrcode python-dateutil dateparser requests

# For Eth address validation and checksum conversion
pip3 install web3

# Credits
Credits for crypto icons: https://github.com/atomiclabs/cryptocurrency-icons 


# Install for build on Linux
git clone https://github.com/smk762/mmbot_qt  
cd mmbot_qt  
python3 -m venv venv   
source venv/bin/activate  
pip3 install -r requirements.txt  
