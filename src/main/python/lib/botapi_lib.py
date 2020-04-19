#!/usr/bin/env python3

import subprocess


def start_botapi(logfile='bot_api_output.log'):
    try:
        bot_api_output = open(config_path+self.username+"_"+logfile,'w+')
        subprocess.Popen(['uvicorn, serve_bot:app, --reload'], stdout=bot_api_output, stderr=bot_api_output, universal_newlines=True)
        time.sleep(1)
    except Exception as e:
        print(e)
