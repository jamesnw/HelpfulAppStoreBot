#!/usr/bin/python

import psutil
import signal

#From https://github.com/getchar/rbb_article

target = "HelpfulAppStore"

# scan through processes
for proc in psutil.process_iter():
    if proc.name() == target:
        print(" match")
        proc.send_signal(signal.SIGUSR1)
