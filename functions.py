import sys
import select
import subprocess
import json
import os
import random
import wget
from datetime import datetime
from math import floor
from hashlib import md5
from os.path import exists as file_exists

from colors import *
from config import SystemConfig, LayoutConfig, MarqueeConfig, GraphLevelsConfig
from lastfm import LastFmConfig
import requests


def get_min_sec(total_secs):
    total_mins = total_secs / 60
    remainder = total_mins - int(total_mins)
    secs = remainder * 60
    return int(total_mins), int(secs)


def get_progress_time(progress, time_len, reversed_timer=False):
    progr_sec = progress / 1000000
    time_len_sec = time_len / 1000000
    progr_min, secs = get_min_sec(progr_sec)
    t_left = time_len_sec - progr_sec

    if t_left == 60:
        min_left = 1
        sec_left = 0
    elif t_left < 60:
        min_left = 0
        sec_left = t_left
    else:
        min_left, sec_left = get_min_sec(t_left)
     
    if reversed_timer:
        return {
            "min": int(min_left),
            "sec": int(sec_left)
        }
    return {
        "min": int(progr_min),
        "sec": int(secs)
    }


def get_volume_color_and_label(volume, max_volume):
    if volume == 0:
        return NC, '🔇'
    vol_color = get_color_by_volume(vol=volume, max_vol=max_volume)
    if 0 < volume <= int(max_volume * .33):
        return vol_color, "🔈"
    if int(max_volume * .33) < volume <= int(max_volume * .66):
        return vol_color, "🔉"
    if int(max_volume * .66) < volume <= int(max_volume * .99):
        return vol_color, "🔊"
    if volume >= int(max_volume * .99):
        return vol_color, "📢"

    return NC, "🔇"


def get_volume_bar(volume):
    volume = int(volume * 100)
    max_volume = 100
    nb_spaces = max_volume - volume
    has_volume_glyph = '―' # █  ■ ⬛  ― █
    has_no_volume = ' '  # ⬜

    color, label = get_volume_color_and_label(volume, max_volume)

    return f'VOL {label} {color}{BOLD}{has_volume_glyph * volume}{has_no_volume * nb_spaces}{NC}'


def get_starting_previous_volume(volume):
    return 0 if volume > 0 else 1


def key_pressed():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def execute_action(c, spotify_bus, reversed_timer, volume, trk_pos, paused, muted, is_shuffle, track_id=None):
    playing = True
    volume_changed = False
    error_msg = ''
    is_local = is_local_track(track_id)
    current_volume = volume

    if c == '\x20': # Spacebar - x1b is ESC
        paused = not paused
        spotify_bus.PlayPause()
    elif c == '\x73':
        is_shuffle = not is_shuffle
        spotify_bus.Shuffle = is_shuffle
    elif c == '\x71': # q
        if not is_local:
            spotify_bus.SetPosition(track_id, (trk_pos - 5000000))
        else:
            error_msg = 'Sorry, operation not permited with local tracks'
    elif c == '\x64': # d
        if not is_local:
            spotify_bus.SetPosition(track_id, (trk_pos + 5000000))
        else:
            error_msg = 'Sorry, operation not permited with local tracks'
    elif c == '\x6e': # n
        spotify_bus.Next()
        playing = False
    elif c == '\x70': # p
        spotify_bus.Previous()
        playing = False
    elif c == '\x78': # x
        reversed_timer = not reversed_timer
    elif c == '\x2b': # +
        if spotify_bus.Volume < 1.0:
            if spotify_bus.Volume >= .98:
                spotify_bus.Volume = 1.0
            else:
                spotify_bus.Volume = spotify_bus.Volume + .02
        volume_changed = True
    elif c == '\x2d': # -
        if spotify_bus.Volume > 0.0:
            if spotify_bus.Volume <= .02:
                spotify_bus.Volume = 0.0
            else:
                spotify_bus.Volume = (spotify_bus.Volume - .02)
        volume_changed = True
    elif c == '\x6d':
        muted = not muted
        current_volume = spotify_bus.Volume
        spotify_bus.Volume = volume

    return playing, reversed_timer, volume_changed, current_volume, error_msg, paused, muted, is_shuffle


def is_local_track(track_id):
    return track_id.startswith('/com/spotify/local/')


def print_error_msg(error_msg):
    print(f'{C_LIGHTCORAL}{error_msg}{NC}', flush=True)


def get_color_by_volume(vol, max_vol, k_min=160, k_max=165):
    nb_ranges = k_max - k_min
    ratio = nb_ranges / max_vol
    vol = (max_vol - vol)
    color_val = int(round(vol * ratio)) + (k_min)
    return f"\033[38;5;{color_val}m"


def display_error_msg(error_msg, e=0, e_c=0):

    error_msg_len = len(error_msg)

    if e < 64:
        error_msg_len = len(error_msg)
        print_error_msg(error_msg)
        e = e + 1
    else:
        if e_c < error_msg_len:
            e_msg = error_msg[e_c:error_msg_len]
            print_error_msg(e_msg)
            e_c = e_c + 2
        else:
            print(flush=True)
            e = e_c = 0
            error_msg = ''

    return e, e_c, error_msg


def display_now_playing(playing_msg, playing_msg_len, show_now_playing, i=0, x=0):

    if i >= 0 and i <= 138:
        print(f'{C_LIME}\033[5m{playing_msg}{NC}', flush=True)
    else:
        if x  >= playing_msg_len:
            x = playing_msg_len
        ply = playing_msg[x:playing_msg_len]
        if i >= 200:
            x = x + 1
        print(f'{C_LIME}{ply}{NC}', flush=True)

    if i == 280:
        show_now_playing = False
        i = 0
    else:
        i = i + 1

    return i, x, show_now_playing


def display_tracks_info(the_string, the_string_len, y, x=0, marquee=False):

    if y <= the_string_len:
        marquee = False
        if the_string_len > 56:
            y = y + 3
        else:
            y = y + 2
    if marquee:
        x = do_marq(the_string, C_GREY74, x)
        return x, y

    print(f"{C_GREY74}{the_string[0:y]}{NC}", flush=True)

    return y


def render_volume_bar(volume_bar, volume, shuffle_icon):
    print(f"{volume_bar} [{volume:03}] {C_LIME}{shuffle_icon}{NC}")


def break_lines(nb_lines = 1):
    for i in list(range(0, nb_lines)):
        print(flush=True) 


def display_date():
    the_date_time = datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M:%S")
    subprocess.run(f'echo "{the_date_time}" | \
        xargs toilet -w 700 -f "small" | \
        lolcat --random --horizontal-frequency 0 --vertical-frequency 1 --seed 1', shell=True)


def get_marq_col_count(the_string_len):
    return LayoutConfig.COLUMN_COUNT if the_string_len < LayoutConfig.COLUMN_COUNT else the_string_len + 1


def get_marq_up(the_string_len):
    marq_col_c = get_marq_col_count(the_string_len)
    return (MarqueeConfig.MARQ_L + ((marq_col_c / MarqueeConfig.SPEED) * MarqueeConfig.ROUNDS))


def pre_generate_marq(the_string, color):
    """
    abcdefghijklmnopqrstuvwxyz  
    bcdefghijklmnopqrstuvwxyz   a
    cdefghijklmnopqrstuvwxyz   ab
    defghijklmnopqrstuvwxyz   abc
    efghijklmnopqrstuvwxyz   abcd
    fghijklmnopqrstuvwxyz   abcde
    ghijklmnopqrstuvwxyz   abcdef
    ...
    """
    the_string = get_marq_string_padding(the_string)
    a_len = len(the_string)
    marq_array = []
    speed = MarqueeConfig.SPEED
    for x in list(range(0, int(a_len / speed))):
        x = int(floor(x * speed))
        marq_array.append(f'{color}{the_string[int(floor(x)):a_len]}{the_string[0:int(floor(x))]}{NC}')

    return marq_array, len(marq_array)



def do_marq_array(marq_array: list, x=0):
    print(marq_array[x])

    return x + 1


def get_marq_string_padding(the_string):
    if len(the_string) >= LayoutConfig.COLUMN_COUNT:
        padding = 1
    else:
        padding = abs(LayoutConfig.COLUMN_COUNT - len(the_string))
    return the_string + (' ' * padding)


def do_marq(the_string, color, x=0, mrq_one=True):
    the_string = get_marq_string_padding(the_string)
    a_len = len(the_string)
    if mrq_one:
        return marq_one(the_string, a_len, x, color)
    return marq_two(the_string, a_len, x, color)


def marq_one(the_string, a_len, x, color):
    """
    abcdefghijklmnopqrstuvwxyz  
    bcdefghijklmnopqrstuvwxyz   a
    cdefghijklmnopqrstuvwxyz   ab
    defghijklmnopqrstuvwxyz   abc
    efghijklmnopqrstuvwxyz   abcd
    fghijklmnopqrstuvwxyz   abcde
    ghijklmnopqrstuvwxyz   abcdef
    ...
    """
    if x == len(the_string):
        x = 0
    print(f'{color}{the_string[int(floor(x)):a_len]}{the_string[0:int(floor(x))]}{NC}', flush=True)
    x = x + .5

    return x


def marq_two(the_string, a_len, x, y, color):

    if x == len(the_string) or y < 0:
        x = 0
        y = a_len - 1
    print(x, a_len)
    print(f'{color}{the_string[x:a_len]} {the_string[y:a_len]}{NC}')
    x = x + 1
    y = y - 1

    return x, y


def last_fm_api_handler(method_call):
    pass


def last_fm_get_api_sig(api_key, method, token, api_secret):
    str_key = f'api_key{api_key}method{method}token{token}{api_secret}'

    return md5(str_key)


def last_fm_call_api(method, body={}, params={}):
    url = LastFmConfig.API_URL

    if method == 'GET':
        res = requests.get(url, params=params)
    elif method == 'POST':
        res = requests.post(url, data=body)

    return res


def last_fm_get_token(api_key):
    method = "auth.gettoken"
    response_format = LastFmConfig.DEFAULT_FORMAT

    return last_fm_call_api('GET', params={
        'method': method,
        'format': response_format
    })


def last_fm_auth(api_key):
    auth_url = LastFmConfig.AUTH_URL
    subprocess.run(f'librewolf --new-window {auth_url}?method=auth.gettoken&api_key={api_key}&format=json')


def last_fm_get_session(api_key, api_secret, token):
    method = "auth.getSession"
    response_format = LastFmConfig.DEFAULT_FORMAT
    sig = last_fm_get_api_sig(api_key=api_key, method=method, token=token, api_secret=api_secret)
    return last_fm_call_api('GET', params={
        'method': method,
        'format': response_format,
        'api_sig': sig,
        "api_key": api_key,
        "token": token
    })


def last_fm_load_session():
    try:
        with open(f"{SystemConfig.CONFIG_STORAGE_PATH}session.json", mode='r') as cfg_file:
            cnt = cfg_file.read()
            return json.loads(cnt)
    except:
        return None


def save_session(session_cnt):
    if not os.path.isdir(SystemConfig.CONFIG_STORAGE_PATH):
        os.mkdir(SystemConfig.CONFIG_STORAGE_PATH)
    with open(f"{SystemConfig.CONFIG_STORAGE_PATH}session.json", mode='w') as cfg_file:
        cfg_file.write(json.dumps(session_cnt))


def last_fm_load_current_session():
    pass


def last_fm_set_now_playing(api_key, sig):
    pass


def last_fm_scrobble_track(api_key, sig):
    pass


def display_vu_meters(fifo_file):
    if not fifo_file:
        display_empty_vu_metters(msg="NO FIFO")
        return
    r1 = fifo_file.readline()
    
    line = r1.split(';')[:12]
    if len(line) < 12:
        display_empty_vu_metters(msg="WRONG DATA")
        return
    c = GraphLevelsConfig.GRAPH_SMALL_GLYPH
    mid1, r, mid2, b, lmid, bass2, bass3, g, h, mid3, j, hmid1 = line
    no_vol = GraphLevelsConfig.GRAPH_EMPTY
    max_volume = SystemConfig.MAX_VOLUME
    try:
        l_color = get_color_from_list(mid1)
        r_color = get_color_from_list(r)
        a_color = get_color_from_list(mid2)
        b_color = get_color_from_list(b)
        bass1_color = get_color_from_list(lmid)
        bass2_color = get_color_from_list(bass2)
        f_color = get_color_from_list(bass3)
        g_color = get_color_from_list(g)
        h_color = get_color_from_list(h)
        i_color = get_color_from_list(mid3)
        j_color = get_color_from_list(j)
        k_color = get_color_from_list(hmid1)
        print(f"[{bass3.zfill(3)}]  {f_color}{c * int(bass3)}{NC}{no_vol * (max_volume - int(bass3))}")
        print(f"[{bass2.zfill(3)}]  {bass2_color}{c * int(bass2)}{NC}{no_vol * (max_volume - int(bass2))}")
        print(f"[{r.zfill(3)}]  {r_color}{c * int(r)}{NC}{no_vol * (max_volume - int(r))}")
        print(f"[{lmid.zfill(3)}]  {bass1_color}{c * int(lmid)}{NC}{no_vol * (max_volume - int(lmid))}")
        print(f"[{b.zfill(3)}]  {b_color}{c * int(b)}{NC}{no_vol * (max_volume - int(b))}")
        print(f"[{mid1.zfill(3)}]  {l_color}{c * int(mid1)}{NC}{no_vol * (max_volume - int(mid1))}")
        print(f"[{mid2.zfill(3)}]  {a_color}{c * int(mid2)}{NC}{no_vol * (max_volume - int(mid2))}")
        print(f"[{mid3.zfill(3)}]  {i_color}{c * int(mid3)}{NC}{no_vol * (max_volume - int(mid3))}")
        print(f"[{g.zfill(3)}]  {g_color}{c * int(g)}{NC}{no_vol * (max_volume - int(g))}")
        print(f"[{hmid1.zfill(3)}]  {k_color}{c * int(hmid1)}{NC}{no_vol * (max_volume - int(hmid1))}")
        print(f"[{h.zfill(3)}]  {h_color}{c * int(h)}{NC}{no_vol * (max_volume - int(h))}")
        print(f"[{h.zfill(3)}]  {j_color}{c * int(h)}{NC}{no_vol * (max_volume - int(h))}")
        
    except ValueError:
        display_empty_vu_metters(msg="EXCEPT")    


def display_empty_vu_metters(msg="NO DATA"):
    msg_len = len(msg)
    is_even = msg_len % 2 == 0
    padding_l = 16 - msg_len
    padding_r = 0
    if padding_l > 0:
        padding_l = int(floor(padding_l / 2))
        padding_r = padding_l if is_even else padding_l + 1
    spacing = " "
    char = '.'
    AMARILLO = f"\033[38;5;190m{BOLD}"
    AZUL = f"\033[38;5;27m{BOLD}"
    ROJO = f"\033[38;5;196m{BOLD}"
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AMARILLO}{char * 40} {NC}__________________{AMARILLO} {char * 40}{NC}")
    print(f"[000]  {AZUL}{char * 40} {NC}|                |{AZUL} {char * 40}{NC}")
    print(f"[000]  {AZUL}{char * 40} {NC}|{spacing * padding_l}{msg}{spacing * padding_r}|{AZUL} {char * 40}{NC}")
    print(f"[000]  {AZUL}{char * 40} {NC}|                |{AZUL} {char * 40}{NC}")
    print(f"[000]  {AZUL}{char * 40} {NC}‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾{AZUL} {char * 40}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")


def display_empty_vu_metters_ve(msg=''):
    char = '.'
    AMARILLO = f"\033[38;5;190m{BOLD}"
    AZUL = f"\033[38;5;27m{BOLD}"
    ROJO = f"\033[38;5;196m{BOLD}"
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AMARILLO}{char * 100}{NC}")
    print(f"[000]  {AZUL}{char * 100}{NC}")
    print(f"[000]  {AZUL}{char * 100}{NC}")
    print(f"[000]  {AZUL}{char * 100}{NC}")
    print(f"[000]  {AZUL}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")
    print(f"[000]  {ROJO}{char * 100}{NC}")



def get_random_color():
    i = random.randint(17, 231)

    return f"\033[38;5;{i}m"

def get_vu_meter_color(val):
    val = int(val) + 17
    return f"\033[38;5;{val}m"

def get_symetric_color(val):
    ratio = int((231 - 17) / 100)
    val = int(val) *  ratio
    if val == 16:
        val = 17
    return f"\033[38;5;{val + 17}m{BOLD}"


def get_color_from_list(vol):
    list_color = GraphLevelsConfig.LIST_COLORS_VOLUME
    max_volume = SystemConfig.MAX_VOLUME
    list_color_len = len(list_color)
    bold = GraphLevelsConfig.GRAPH_BOLD
    ratio =  max_volume / list_color_len
    
    val = int(float(vol) / ratio)
    if val >= list_color_len:
        val = val - 1
    try:
        # print(val, list_color_len, ratio, vol)
        return f'\033[38;5;{list_color[val]}m{bold}'
    except IndexError as e:
        # print_exception(e)
        print(val, list_color_len, ratio, vol)
        raise e
    

def album_art_exists(track_id: str):
    fle_path = f'{SystemConfig.ALBUM_ART_PATH}{track_id}.sxl'
    if file_exists(fle_path):
        return fle_path
    return None


def get_album_art(album_art_url, track_id: str):
    if is_local_track(track_id):
        return None
    
    album_art_id = album_art_url.split('/')[:3:-1][0]
    fle_sxl = album_art_exists(album_art_id)
    
    if not fle_sxl:
        fle_path = download_album_art(album_art_url, album_art_id)
        fle_path = resize_image(fle_path, album_art_id)
        fle_sxl = convert_image_to_sixel(fle_path, album_art_id)
    return fle_sxl


def resize_image(fle_path, album_art_id):
    fle_resize = f'{SystemConfig.ALBUM_ART_PATH}{album_art_id}_60x60.jpg'
    subprocess.run(f'ffmpeg -hide_banner -loglevel panic -i {fle_path} -vf scale=60:60 {fle_resize} > /dev/null', shell=True)
    subprocess.run(f'rm -f {fle_path}', shell=True)
    return fle_resize


def convert_image_to_sixel(fle_path, album_art_id):
    sxl_path = f"{SystemConfig.ALBUM_ART_PATH}/{album_art_id}.sxl"
    subprocess.run(f"img2sixel {fle_path} > {sxl_path}", shell=True)
    return sxl_path


def download_album_art(album_art_url, album_art_id):
    fle_path = f'{SystemConfig.ALBUM_ART_PATH}{album_art_id}.jpg'
    wget.download(album_art_url, out=fle_path, bar=None)

    return fle_path


def get_image_sixel(album_art_id):
    return f'{SystemConfig.ALBUM_ART_PATH}{album_art_id}.sxl'


def render_album_art(sxl_path=None):
    if not sxl_path:
        sxl_path = SystemConfig.GENERIC_ALBUM_ART_PATH
    subprocess.run(f"cat {sxl_path}", shell=True)



