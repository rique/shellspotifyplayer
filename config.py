from colors import NC, BOLD
class MarqueeConfig:
    MARQ_X = 0 # Marquee effect key
    MARQ_C = 0 # Marquee effect actif
    MARQ_L = 2380
    SPEED = 1/3
    ROUNDS = 1


class LayoutConfig:
    COLUMN_COUNT = 115


class AliveBarConfig:
    SPINNER = 'radioactive'
    LENGTH = 114


class SystemConfig:
    CONFIG_STORAGE_PATH = "~/.config/sp_player/"
    SLEEP = .008
    FIFO_PATH = '/tmp/cava'
    MAX_VOLUME = 115
    VOLUM_BAR_MAX_VOLUME = 100
    BASE_PATH = '/home/enriaue/.local/lib/show_date/spotify_player/'
    ALBUM_ART_PATH = '/home/enriaue/.local/lib/show_date/spotify_player/albumarts/'
    GENERIC_ALBUM_ART_PATH = '/home/enriaue/.local/lib/show_date/spotify_player/albumarts/generic.sxl'


class GraphLevelsConfig:
    LIST_COLORS_VOLUME = [ '184', '179', '178', '172', '166', '209', '208', '204', '203', '202','165', '164', '163', '129', '128', '127', '126', '171', '170', '169', '201', '200', '199', '162', '198', '161', '197', '161', '196', '160']
    # LIST_COLORS_VOLUME = ['184', '190', '179', '178', '167', '166', '209', '208', '171', '129', '128', '127', '126', '141', '140', '135', '165', '164', '163', '162', '161', '160', '196']
    GRAPH_EMPTY = ''
    GRAPH_GLYPH = '█'
    GRAPH_SMALL_GLYPH = '▌' # ▏▎▍▌▋▊▉█
    GRAPH_DOT = '.'
    GRAPH_LINE = '―'
    GRAPH_BOLD = ''



