import subprocess
import platform
import logging
import time
import requests

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# Attempt to suppress console window in windows version. TODO: not working, find another way.
if platform.system() == 'Windows':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
else:
    startupinfo = None

# start MM2 for specific user
def start_mm2(mm2_bin, config_path, username, logfile='mm2_output.log'):
    try:
        mm2_output = open(config_path+username+"_"+logfile,'w+')
        mm2_proc = subprocess.Popen([mm2_bin], stdout=mm2_output, stderr=mm2_output, universal_newlines=True, startupinfo=startupinfo)
        time.sleep(0.5)
    except Exception as e:
        logger.info(e)
        logger.info("MM2 Binary did not start!")

def start_api(api_bin, config_path, username, logfile='bot_api_output.log'):
    try:
        bot_api_output = open(config_path+username+"_"+logfile,'w+')
        api_proc = subprocess.Popen([api_bin, config_path], stdout=bot_api_output, stderr=bot_api_output, universal_newlines=True, startupinfo=startupinfo)
        time.sleep(0.5)
    except Exception as e:
        logger.info(e)
        logger.info("MM2 Bot API did not start!")

def auth_api(mm2_ip, mm2_pass, key, secret, username):
    if key == '':
        key = 'x'
    if secret == '':
        secret = 'x'
    endpoint = 'http://127.0.0.1:8000/set_creds?'
    params = 'ip='+mm2_ip+'&rpc_pass='+mm2_pass+'&key='+key+'&secret='+secret+'&username='+username
    url = endpoint+params
    requests.post(url)

def kill_api():
    logger.info("Kill api_proc")
    if platform.system() == 'Windows':
        kill_api = subprocess.Popen(["tskill", "mmbot_api.exe"], startupinfo=startupinfo)
    else:
        kill_api = subprocess.Popen(["pkill", "-9", "mmbot_api"], startupinfo=startupinfo)
    kill_api.wait()

def kill_mm2():
    logger.info("Kill mm2_proc")
    if platform.system() == 'Windows':
        kill_mm2 = subprocess.Popen(["tskill", "mm2.exe"], startupinfo=startupinfo)
    else:
        kill_mm2 = subprocess.Popen(["pkill", "-9", "mm2"], startupinfo=startupinfo)
    kill_mm2.wait()

def purge_mm2_json(config_path):
    with open(config_path+"MM2.json", 'w+') as j:
        j.write('')