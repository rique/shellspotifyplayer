import os
import subprocess
import termios
import tty
import sys

from pydbus import SessionBus

from config import SystemConfig 
from functions import get_starting_previous_volume
from colors import *

def setup_app():
    try:
        os.mkfifo(SystemConfig.FIFO_PATH)
    except FileExistsError:
        pass

    subprocess.call("cava &>/dev/null &", shell=True)

    old_settings = termios.tcgetattr(sys.stdin)
    session_bus = SessionBus()

    spotify_bus = session_bus.get(
        "org.mpris.MediaPlayer2.spotify", # Bus name
        "/org/mpris/MediaPlayer2" # Object path
    )

    spotify_bus.Play()

    playing_msg = 'NOW PLAYING'
    playing_msg_len = len(playing_msg)

    tty.setcbreak(sys.stdin.fileno())

    reversed_timer = True
    
    is_shuffle = spotify_bus.Shuffle
    # shuffle_icon = chr(0x1F500) if is_shuffle else ''
    shuffle_icon = f' {SHUFFLE_ON}{NC}' if is_shuffle else f' {SHUFFLE_OFF}{NC}'
    previous_volue = get_starting_previous_volume(spotify_bus.Volume)
    fifo_file =  open(SystemConfig.FIFO_PATH)

    return spotify_bus, playing_msg, playing_msg_len, reversed_timer, is_shuffle, shuffle_icon, previous_volue, fifo_file, old_settings
