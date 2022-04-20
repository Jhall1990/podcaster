# The rss feed for the youtube channel to convert to podcast.
# Format should be something like https://www.youtube.com/feeds/videos.xml?channel_id=<channel_id>"
# You can get the <channel_id> from the channel's page on youtube.
YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCpXBGqwsBkpvcYjsJBQ7LEQ"

# The regex to identify episodes to convert to podcast.
EPISODE_RE = r"(.*?)\s\|\sCritical Role\s\|\sCampaign\s\d+,\sEpisode\s(\d+)"

# The location (folder) where the downloaded episodes should be saved.
# Example: /home/user/downloads/
EPISODE_LOCATION = "/mnt/nas/storage/ftp/programs/podcaster/episodes"

# The location (file) where the podcast rss file should be saved.
# /home/user/podcast/pod.xml
XML_LOCATION = "/mnt/nas/storage/ftp/programs/podcaster/pod.xml"

# The url prefix where the episodes will be hosted.
# Example: http://192.168.1.100/episodes
EPISODE_URL_PREFIX = "http://freya.home:81/storage/ftp/programs/podcaster/episodes/"

# Metadata about your podcast, this will be put into the generated podcast xml (rss)
# file. Most of this doesn't really matter as you're probably not putting this podcast
# out for the rest of the world to see.
PODCAST_INFO = {
        "title": "Local Critical Role",
        "url": "youtube.com",
        "desc": "Critical Role",
        "category": "DND",
        "email": "jacobhall90@gmail.com"
    }
