from colors import NC, BOLD
class MarqueeConfig:
    MARQ_X = 0 # Marquee effect key
    MARQ_C = 0 # Marquee effect actif
    MARQ_L = 2110
    SPEED = .25
    ROUNDS = 1


class LayoutConfig:
    COLUMN_COUNT = 100


class AliveBarConfig:
    SPINNER = 'radioactive'
    LENGTH = 99


class SystemConfig:
    CONFIG_STORAGE_PATH = "~/.config/sp_player/"
    SLEEP = .008
    # FIFO_PATH = '/home/enriaue/.local/lib/show_date/pipewire/vol'
    FIFO_PATH = '/tmp/vol'
    MAX_VOLUME = 128
    BASE_PATH = '/home/enriaue/.local/lib/show_date/spotify_player/'
    ALBUM_ART_PATH = '/home/enriaue/.local/lib/show_date/spotify_player/albumarts/'
    GENERIC_ALBUM_ART_PATH = '/home/enriaue/.local/lib/show_date/spotify_player/albumarts/generic.sxl'


class GraphLevelsConfig:
    LIST_COLORS_VOLUME = [ '184', '179', '178', '166', '209', '208', '204', '203', '202','165', '164', '163', '129', '128', '127', '126', '171', '170', '169', '201', '200', '199', '162', '198', '161', '197', '196', '125', '124', '160']
    GRAPH_EMPTY = ''
    GRAPH_GLYPH = '█'
    GRAPH_SMALL_GLYPH = '▌' # ▏▎▍▌▋▊▉█
    GRAPH_DOT = '.'
    GRAPH_LINE = '―'
    GRAPH_BOLD = ''



