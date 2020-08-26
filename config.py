# The rss feed for the yoututbe channel to convert to podcast.
# Format should be something like https://www.youtube.com/feeds/videos.xml?channel_id=<channel_id>"
# You can get the <channel_id> from the channel's page on youtube.
YOUTUBE_RSS = ""

# The regex to identify episodes to convert to podcast.
EPISODE_RE = r""

# The location (folder) where the downloaded episodes should be saved.
# Example: /home/user/downloads/
EPISODE_LOCATION = ""

# The location (file) where the podcast rss file should be saved.
# /home/user/podcast/pod.xml
XML_LOCATION = ""

# The url prefix where the episodes will be hosted.
# Example: http://192.168.1.100/episodes
EPISODE_URL_PREFIX = ""

# Metadata about your podcast, this will be put into the generated podcast xml (rss)
# file. Most of this doesn't really matter as you're probably not putting this podcast
# out for the rest of the world to see.
PODCAST_INFO = {
        "title": "podcast title",
        "url": "www.podcasturl.com",
        "desc": "description of podcast",
        "category": "podcast category",
        "email": "some_email@email.com"
    }
