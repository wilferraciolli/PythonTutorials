from datetime import timedelta

# Name of the `_data` block in the response envelope for the timeline API.
POSTS_DATA_NAME = "posts"

# Link relation names: meta links (`_metaLinks`).
LINK_SELF = "self"
LINK_TIMELINE_ALL = "timelineAll"
LINK_TIMELINE_FOLLOWING = "timelineFollowing"
LINK_TIMELINE_POPULAR = "timelinePopular"

WINDOW = timedelta(days=365)
DEFAULT_LIMIT = 50
MAX_LIMIT = 100
