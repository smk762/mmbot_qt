# mmbot_qt
MarketMaker2 BobBot GUI for pythonQT  

## Dependancies
sudo apt-get install python3.6 python3-pip libgnutls28-dev python3-venv python3-dev libpython3-dev libevent-dev libssl-dev libcurl4-openssl-dev  
pip3 install -r requirements.txt  

### For building installer
sudo apt-get install ruby ruby-dev rubygems build-essential (for building installer)  
gem install --no-document fpm

### For Eth address validation and checksum conversion  (pending)
pip3 install web3  

# Credits  
Credits for crypto icons: https://github.com/atomiclabs/cryptocurrency-icons 


# Install for build on Linux  
git clone https://github.com/smk762/mmbot_qt  
cd mmbot_qt  
python3 -m venv venv   
source venv/bin/activate  
fbs freeze  
fbs installer  

### remove old pkg
sudo dpkg --purge mm2-maker-bot

### install new pkg
sudo dpkg -i target/mm2-maker-bot.deb
