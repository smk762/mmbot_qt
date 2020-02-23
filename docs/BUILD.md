Build instructions below. Using fman build system (https://github.com/mherrmann/fbs-tutorial)
Assumes Python 3 already installed.

# Linux Setup

Clone repo
```
sudo apt update 
sudo apt-get install python3-venv libcurl4-gnutls-dev python3-dev
cd
git clone https://github.com/smk762/mmbot_qt
cd mmbot_qt
```

Create a virtual environment in the current directory:

`python3 -m venv venv`

Activate the virtual environment:

`source venv/bin/activate`

Install dependancies

`pip3 install -r requirements.txt`

OS specific mm2 binaries are also required to be placed in the `mmbot_qt/src/main/resources/linux` folder (or other OS folder depending on build OS).

If all went according to plan, you should now be able to execute `fbs run` to load the app.

Follow the readme at https://github.com/smk762/mmbot_qt/blob/style/docs/README.rst to create a user, setup seed etc, log back in and activate some coins. 

If anything goes wrong, it should be traceable in the console.

If all goes well, you can freeze the app with `fbs freeze`, which will create a portable version in the mmbot_qt/target folder.

To create a .deb installer file, run `fbs installer`

Creating an installer on Mac/Win is very much the same as the above, with some slight changes in activating the virtual environment or installing fman (refer to https://github.com/mherrmann/fbs-tutorial for details)


# Notes:
use python 3.6.x
mac requires pyinstaller==3.4
windows needs additional dlls (more info to come)
windows needs hiddenimport for (more info to come)
