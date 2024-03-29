#!/usr/bin/python -u

import os
import sys
import tty
import termios
import subprocess
from traceback import print_exception

from functions import *
from config import MarqueeConfig, AliveBarConfig, SystemConfig

from alive_progress import alive_bar
from time import sleep
from pydbus import SessionBus


def main():
    try:
        os.mkfifo(SystemConfig.FIFO_PATH)
    except FileExistsError:
        pass

    subprocess.run("cava &", shell=True)

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
    shuffle_icon = '🔀' if is_shuffle else ''

    previous_volue = get_starting_previous_volume(spotify_bus.Volume)
    fifo_file =  open(SystemConfig.FIFO_PATH)
    while True:
        try:
            os.system('clear')
            metadata = spotify_bus.Metadata
            track_length = metadata['mpris:length']

            artist = metadata['xesam:artist'][0]
            track_title = metadata['xesam:title']
            album = metadata['xesam:album']
            track_id = metadata['mpris:trackid']

            album_art_sxl_path = get_album_art(metadata['mpris:artUrl'], track_id)

            nb_secs = (track_length / 1000000)
            nb_min, secs = get_min_sec(nb_secs)
            track_time = f"{nb_min:02}:{secs:02}"

            the_string = f"{artist} ~ {track_title} ~ ({album}) [{track_time}]"
            the_string_len = len(the_string)
            volume_bar = get_volume_bar(spotify_bus.Volume)
            
            marq_array, marq_len = pre_generate_marq(the_string, color=C_GREY74)

            i = 0 # "Playing Next" display sync
            x = 0 # "Playing Next" animation Sync
            y = 1 # "Track Info display" animation sync
            e = 0 # "Error Msg" display sync
            e_c = 0 # "Error Msg" display counter
            marq_x = MarqueeConfig.MARQ_X # Marquee effect key
            marq_c = MarqueeConfig.MARQ_C # Marquee effect actif
            marq_l = MarqueeConfig.MARQ_L
            marq_up = get_marq_up(the_string_len)

            current_volume = spotify_bus.Volume

            display_date()

            break_lines(3)

            playing = True
            show_now_playing = True
            paused = spotify_bus.PlaybackStatus == 'Paused'
            muted = current_volume == 0

            error_msg = ''

            with alive_bar(100,
                    spinner=AliveBarConfig.SPINNER,
                    bar='smooth',
                    manual=True,
                    elapsed=False,
                    stats=False,
                    enrich_print=True,
                    monitor=False,
                    length=AliveBarConfig.LENGTH,
                    dual_line=True
                ) as bar:
                while playing:
                    trk_pos = spotify_bus.Position
                    cur_track_id = spotify_bus.Metadata['mpris:trackid']
                    try:
                        percent_pos = int((trk_pos / track_length) * 1000)
                    except ZeroDivisionError:
                        playing = False
                        continue

                    if cur_track_id != track_id:
                        playing = False
                        continue

                    if current_volume != spotify_bus.Volume:
                        volume_bar = get_volume_bar(spotify_bus.Volume)
                        current_volume = spotify_bus.Volume

                    if is_data():
                        playing, reversed_timer, change_volume, previous_volue, error_msg, paused, muted, is_shuffle = execute_action(sys.stdin.read(1), spotify_bus, reversed_timer, previous_volue, trk_pos, paused, muted, is_shuffle, track_id)
                        if change_volume:
                            volume_bar = get_volume_bar(spotify_bus.Volume)
                        if not playing:
                            continue
                        if paused and not muted:
                            if fifo_file:
                                fifo_file.close()
                                fifo_file = None
                        elif not muted:
                            if not fifo_file:
                                fifo_file = open(SystemConfig.FIFO_PATH)
                        if muted and not paused:
                            if fifo_file:
                                fifo_file.close()
                                fifo_file = None
                        elif not paused:
                            if not fifo_file:
                                fifo_file = open(SystemConfig.FIFO_PATH)
                        shuffle_icon = '🔀' if is_shuffle else ''

                    progr = percent_pos / 1000

                    if  progr > 1:
                        playing = False
                        progr = 1

                    timers = get_progress_time(trk_pos, track_length, reversed_timer=reversed_timer)
                    
                    bar.title(f"{timers['min']:02}:{timers['sec']:02}")
                    bar(progr)

                    sleep(SystemConfig.SLEEP)

                    if cur_track_id != track_id:
                        playing = False
                        continue

                    subprocess.run('clear', shell=True)

                    display_date()

                    if error_msg != "" or show_now_playing:
                        if show_now_playing:
                            i, x, show_now_playing = display_now_playing(playing_msg, playing_msg_len, show_now_playing, i, x)
                        else:
                            e, e_c, error_msg = display_error_msg(error_msg, e, e_c)
                    else:
                        break_lines()
                    
                    if marq_l <= marq_c <= marq_up:
                        if marq_c == (marq_up - 1):
                            marq_c = 0
                            marq_x = 0
                        
                        marq_x = do_marq_array(marq_array, marq_x)
                    else:
                        y = display_tracks_info(the_string, the_string_len, y)

                    # break_lines(2)
                    # render_album_art(album_art_sxl_path)
                    
                    break_lines(2)
                    display_vu_meters(fifo_file)
                    break_lines(2)

                    volume = int(round(spotify_bus.Volume * 100))
                    render_volume_bar(volume_bar, volume, shuffle_icon)

                    break_lines()
                    marq_c = marq_c + 1
                    
        except (KeyboardInterrupt):
            print("Good Bye")
            if fifo_file:
                fifo_file.close()
                fifo_file = None
            try:
                os.unlink(SystemConfig.FIFO_PATH)
            except Exception as e:
                print(e)
                print()
                pass

            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            sleep(.5)
            exit(0)
        except Exception as e:
            if fifo_file:
                fifo_file.close()
                fifo_file = None
            try:
                os.unlink(SystemConfig.FIFO_PATH)
            except Exception as e2:
                print(e2)
                print()
                pass

            print('An error occured! Exiting!')
            print()
            print_exception(e)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            sleep(.5)
            exit(1)

if __name__ == "__main__":
    main()

