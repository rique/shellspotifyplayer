#!/usr/bin/python -u

import os
import sys
import termios
import subprocess
from traceback import print_exception

from functions import (
                    display_date,
                    get_album_art,
                    get_album_art_data,
                    get_min_sec,
                    get_volume_bar,
                    pre_generate_marq,
                    get_marq_up,
                    break_lines,
                    key_pressed,
                    execute_action,
                    get_progress_time,
                    display_now_playing,
                    display_error_msg,
                    do_marq_array,
                    display_tracks_info,
                    display_vu_meters,
                    render_volume_bar,
                    print_graph
            )
from config import MarqueeConfig, AliveBarConfig, SystemConfig

from alive_progress import alive_bar
from time import sleep
from app_functions import setup_app, start_cava, kill_cava

from colors import TITLE_GREY, NC, SHUFFLE_OFF, SHUFFLE_ON


def main():
    spotify_bus, playing_msg, playing_msg_len, reversed_timer, is_shuffle, shuffle_icon, previous_volue, fifo_file, old_settings = setup_app()
    volume_values = []
    sleeptime = SystemConfig.SLEEP
    paused = spotify_bus.PlaybackStatus == 'Paused'
    while True:
        try:
            subprocess.run('clear', shell=True)
            metadata = spotify_bus.Metadata
            track_length = metadata['mpris:length']

            artist = metadata['xesam:artist'][0]
            track_title = metadata['xesam:title']
            album = metadata['xesam:album']
            track_id = metadata['mpris:trackid']

            album_art_sxl_path = get_album_art(metadata['mpris:artUrl'], track_id)
            album_art_data = get_album_art_data(album_art_sxl_path)
            
            
            nb_secs = (track_length / 1000000)
            nb_min, secs = get_min_sec(nb_secs)
            track_time = f"{nb_min:02}:{secs:02}"

            # the_string = f"{artist} ～ {track_title} ～ ({album}) [{track_time}]"
            track_song_info = f"{track_title} ~ ({album}) [{track_time}]"
            track_info_len = len(track_song_info)
            artist_info = f"Artist: {TITLE_GREY}{artist}{NC}"
            volume_bar = get_volume_bar(spotify_bus.Volume)
            
            marq_array, marq_len = pre_generate_marq(track_song_info, color=TITLE_GREY)

            i = 0 # "Playing Next" display sync
            x = 0 # "Playing Next" animation Sync
            y = 1 # "Track Info display" animation sync
            e = 0 # "Error Msg" display sync
            e_c = 0 # "Error Msg" display counter
            marq_x = MarqueeConfig.MARQ_X # Marquee effect key
            marq_c = MarqueeConfig.MARQ_C # Marquee effect actif
            marq_l = MarqueeConfig.MARQ_L
            marq_up = get_marq_up(track_info_len)
            
            max_cols = SystemConfig.MAX_COLS
            array_key_up = 1
            array_key_down = 0
            graph_counter = 0

            current_volume = spotify_bus.Volume

            display_date()

            break_lines(3)
            # weather = open('/home/enriaue/.stuff/tempe_sp').readline()
            playing = True
            show_now_playing = True
            
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
                        percent_pos = (trk_pos / track_length) * 1000
                    except ZeroDivisionError:
                        playing = False
                        continue
                    
                    if percent_pos == 0:
                        playing = False
                        continue

                    if current_volume != spotify_bus.Volume:
                        volume_bar = get_volume_bar(spotify_bus.Volume)
                        current_volume = spotify_bus.Volume

                    if key_pressed():
                        playing, reversed_timer, volume_changed, previous_volue, error_msg, paused, muted, is_shuffle = execute_action(sys.stdin.read(1), spotify_bus, reversed_timer, previous_volue, trk_pos, paused, muted, is_shuffle, track_id)
                        if volume_changed:
                            volume_bar = get_volume_bar(spotify_bus.Volume)
                        
                        if paused:
                            sleeptime = SystemConfig.PAUSE_SLEEP
                        else:
                            sleeptime = SystemConfig.SLEEP
                        if paused and not muted:
                            kill_cava()
                            if fifo_file:
                                fifo_file.close()
                                fifo_file = None
                                
                        elif not muted:
                            if not fifo_file:
                                start_cava()
                                fifo_file = open(SystemConfig.FIFO_PATH)
                        if muted and not paused:
                            kill_cava()
                            if fifo_file:
                                fifo_file.close()
                                fifo_file = None
                                
                        elif not paused:
                            if not fifo_file:
                                start_cava()
                                fifo_file = open(SystemConfig.FIFO_PATH)
                        shuffle_icon = f' {SHUFFLE_ON}{NC}' if is_shuffle else f' {SHUFFLE_OFF}{NC}'
                        if not playing:
                            continue
                    progr = percent_pos / 1000

                    timers = get_progress_time(trk_pos, track_length, reversed_timer=reversed_timer)
                    
                    bar.title(f"{timers['min']:02}:{timers['sec']:02}")
                    bar(progr)

                    sleep(sleeptime)

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
                        y = display_tracks_info(track_song_info, track_info_len, y)
                    print(artist_info)
                    # break_lines(2)
                    #if render_album:
                    # render_album_art(t=(trk_pos / 1000), sxl_path=album_art_sxl_path)
                    # render_album = False
                    # test_album_art()
                    """print()
                    print(f"The weather:  {weather}")"""
                    # print(f"{album_art_data}{NC}")
                    break_lines(2)
                    display_vu_meters(fifo_file)
                    # volume_values.append(vol_val)

                    

                    # break_lines(2)
                    # print_graph(volume_values, SystemConfig.MAX_COLS)
                    
                    """if array_key_up >= max_cols:
                        volume_values.pop(0)

                    array_key_up += 1"""
                    break_lines(2)
                    volume = int(round(spotify_bus.Volume * SystemConfig.VOLUM_BAR_MAX_VOLUME))
                    render_volume_bar(volume_bar, volume, shuffle_icon)

                    break_lines()
                    marq_c = marq_c + 1
                    
        except KeyboardInterrupt:
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

