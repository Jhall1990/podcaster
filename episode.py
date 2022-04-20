import os
import re
import config
import pytube
import threading
import feedparser


def get_episodes(rss_link, episode_re):
    """
    Get's all the episodes from the provided rss_link. Only episodes titles
    that match the provided episode_re will be returned.
    """
    episodes_ = []
    feed = feedparser.parse(rss_link)
    for entry in feed.entries:
        match = re.search(episode_re, entry.title)
        if match:
            title_ = match.group(1)
            number_ = match.group(2)
            link_ = entry.links[0].href
            print("Found episode {}...".format(title_))
            episodes_.append(Episode(title_, number_, link_))

    return episodes_


def download_episodes(episodes):
    """
    Starts a thread for each download, waits for them to compelete, then
    renames each of the episodes.
    """
    threads = []

    # Start all the threads.
    for episode in episodes:
        threads.append(episode.download())

    # Wait for all the threads.
    for thread in threads:
        thread.join()

    # Rename each downloaded file.
    for episode in episodes:
        episode.rename()


class Episode(object):
    """
    An episode object holds all the information about a given youtube video episode.
    """
    def __init__(self, title, number=None, yt_link=None):
        self.title = title
        self.number = number
        self.yt_link = yt_link
        self.file_name = "{}.mp4".format(self.title.replace(" ", "_").replace(",", "").lower())
        self.file_location = os.path.join(config.EPISODE_LOCATION, self.file_name)
        self.local_link = "{}{}".format(config.EPISODE_URL_PREFIX, self.file_name)
        self.download_thread = None

    def __hash__(self):
        """
        Used when converting a list of episodes into a set. Which is done to diff
        episode lists.
        """
        return self.title.__hash__()

    def __eq__(self, other):
        """
        Consider an episode object equal to another if it has the same title. Epsiode
        objects can have different data depending on whether it's created from a newly
        downloaded episode or an existing episode.
        """
        if not isinstance(other, Episode):
            return False
        if self.title != other.title:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def size(self):
        """
        The podcast rss file requires the filesize, this gets the file's size.
        """
        if os.path.exists(self.file_location):
            return os.path.getsize(self.file_location)
        else:
            return 0

    def download(self):
        """
        Handles creating the download thread and starting it. Returns the thread so
        that it can be joined later.
        """
        yt = pytube.YouTube(self.yt_link)
        stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
        self.download_thread = DownloadThread(stream)

        print("Starting download of {}...".format(self.title))

        self.download_thread.start()
        return self.download_thread

    def rename(self):
        """
        Move the downloaded episode from wherever it was downloaded to location
        specified in the config file.
        """
        os.rename(self.download_thread.location, self.file_location)


class DownloadThread(threading.Thread):
    def __init__(self, stream):
        super(DownloadThread, self).__init__()
        self.stream = stream
        self.done = False
        self.error = ""
        self.location = ""

    def run(self):
        """
        Try to download the episode specified in the thread, mark it done when it finishes.
        I know, bare except is gross, but this was really only a personal project so cut me
        some slack :).
        """
        try:
            self.location = self.stream.download(config.EPISODE_LOCATION)
        except Exception as e:
            self.error = e
        self.done = True
