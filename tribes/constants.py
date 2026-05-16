"Game-wide constants ported from Constants.java."

LOG_STATS: bool = True
VERBOSE: bool = True
VISUALS: bool = True
WRITE_SAVEGAMES: bool = False
DISABLE_NON_HUMAN_GRID_HIGHLIGHT: bool = True
FRAME_DELAY: int = 0
TURN_TIME_LIMITED: bool = False
TURN_TIME_MILLIS: int = 10_000_000
GUI_INFO_DELAY: int = 0
GUI_PAN_TO_TRIBE: bool = False

# Display settings (set dynamically by GUI init)
GUI_GAME_VIEW_SIZE: int = 0
CELL_SIZE: int = 0
GUI_MIN_PAN: int = 0
GUI_COMP_SPACING: int = 0
GUI_CITY_TAG_WIDTH: int = 0
GUI_DRAW_EFFECTS: bool = False

GUI_SIDE_PANEL_WIDTH: int = 0
GUI_INFO_PANEL_HEIGHT: int = 0
GUI_ACTION_PANEL_HEIGHT: int = 0
GUI_TECH_PANEL_HEIGHT: int = 0
GUI_ACTION_PANEL_FULL_SIZE: int = 350
GUI_TECH_PANEL_FULL_SIZE: int = 300

SHADOW_OFFSET: int = 1
ROUND_RECT_ARC: int = 5
GUI_ZOOM_FACTOR: int = 5

# Turn limits
MAX_TURNS: int = 30
MAX_TURNS_CAPITALS: int = 50
PLAY_WITH_FULL_OBS: bool = True
GUI_FORCE_FULL_OBS: bool = True
