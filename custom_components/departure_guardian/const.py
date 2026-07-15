DOMAIN = "departure_guardian"

CONF_ALARM_ENTITY = "alarm_entity"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_WATCHED_ENTITIES = "watched_entities"

CONF_ENTITY_ID = "entity_id"
CONF_KIND = "kind"
CONF_PROBLEM_STATE = "problem_state"
CONF_THRESHOLD = "threshold"
CONF_LABEL = "label"

KIND_BINARY = "binary"
KIND_POWER = "power"

DEFAULT_PROBLEM_STATE = "on"
DEFAULT_THRESHOLD = 5.0

ARMING_STATES = ("arming",)
ARMED_STATES = (
    "armed_home",
    "armed_away",
    "armed_night",
    "armed_vacation",
    "armed_custom_bypass",
)

CONF_MAP_CAMERA = "map_camera"
CONF_MAP_IMAGE = "map_image"
CONF_POSITIONS = "positions"
CONF_X = "x"
CONF_Y = "y"

STATIC_URL_BASE = "/departure_guardian_static"
MAP_CARD_FILENAME = "departure-guardian-map-card.js"
