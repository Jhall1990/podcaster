import os
import re
import sys
import pydub
import config
import ffmpeg
import pytube
import string
import hashlib
import requests
import threading
import feedparser
import subprocess
from mutagen.mp4 import MP4

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
            yt_id = entry.yt_videoid
            print("Found episode {}...".format(title_))
            episodes_.append(Episode(title_, number_, link_, yt_id))

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
        episode.remove_sponsors()

class Episode(object):
    """
    An episode object holds all the information about a given youtube video episode.
    """
    def __init__(self, title, number=None, yt_link=None, yt_id=None):
        self.title = self.norm_title(title)
        self.number = number
        self.yt_link = yt_link
        self.yt_id = yt_id
        self.file_name = self.get_filename(title)
        self.file_location = os.path.join(config.EPISODE_LOCATION, self.file_name)
        self.local_link = "{}{}".format(config.EPISODE_URL_PREFIX, self.file_name)
        self.download_thread = None
        self.ffmpeg_inp_file = "inp.txt"

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

    def norm_title(self, title):
        """
        Normalize the episode title so it can be converted to xml without illegal chars.
        """
        illegal = [ ("&", "and") ]

        for illegal_char, replace in illegal:
            if illegal_char in title:
                title = title.replace(illegal_char, replace)
        return title

    def get_filename(self, title):
        """
        Get the name of the file for ffmpeg, remove punctuation and replace spaces
        with underscores
        """
        no_punc = title.translate(str.maketrans("", "", string.punctuation))
        to_lower = no_punc.lower()
        no_space = to_lower.replace(" ", "_")
        return "{}.mp4".format(no_space)

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

    def remove_sponsors(self):
        """
        See if the sponsor block API knows anything about this episode. If it
        does slice up the audio and remove the sponsor sections.
        """
        print( "Removing ads from {}".format( self.file_name ) )
        sponsor_segments = self.get_sponsor_blocks()
        norm_segments = self.normalize_segments(sponsor_segments)
        segments = self.get_segments(norm_segments)
        split_files = self.split_audio(segments)
        self.join_audio(split_files)

    def normalize_segments(self, segments):
        norm_segments = []
        idx = 0

        while idx < len(segments):
            jdx = idx + 1
            start = segments[idx][0]
            end = segments[idx][1]

            while jdx < len(segments):
                startNext = segments[jdx][0]
                if startNext == end:
                    end = segments[jdx][1]
                    segments.pop(jdx)
                else:
                    break
            idx += 1
            norm_segments.append((start, end))
        return norm_segments
        
    def yt_id_hash(self):
        """
        Get the first 4 of the sha256 hash of the video id
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(self.yt_id.encode("utf-8"))
        return sha256_hash.hexdigest()[:4]

    def get_sponsor_blocks(self):
        """
        Make a get request tohttps://sponsor.ajay.app/api/skipSegments/<first_4_of_sum> 
        for all sponsor block info for the video.
        """
        id_hash = self.yt_id_hash()
        sponsor_info_list = requests.get("https://sponsor.ajay.app/api/skipSegments/{}".format(id_hash)).json()

        for sponsor_info in sponsor_info_list:
            if sponsor_info["videoID"] == self.yt_id:
                return [i["segment"] for i in sponsor_info["segments"]]
        return []

    def get_segments(self, sponsor_segments):
        """
        Get the segments of the audio without sponsors. We'll use
        ffmpeg to create clips of these segments then concat them
        back into one file.
        """
        segments = []
        cur_pos = 0
        audio_len = int(MP4(self.file_location).info.length)

        for index, (start, end) in enumerate(sponsor_segments):
            if start == 0:
                cur_pos = end
                continue

            segments.append([cur_pos, start])
            cur_pos = end

            if index == len(sponsor_segments) - 1:
                segments.append([cur_pos, audio_len])
        return segments

    def split_audio(self, segments):
        """
        Use ffmpeg to split the audio into multiple parts excluding the
        segments identified by sponsor block.
        """
        files = []

        for index, (start, end) in enumerate(segments):
            dur = end - start
            file_name = "{}_{}".format(self.file_name, index)
            stream = ffmpeg.input(self.file_location, ss=start, t=dur)
            stream = ffmpeg.output(stream, file_name, f="mp4")
            ffmpeg.run(stream)
            files.append(file_name)
        return files

    def join_audio(self, files):
        """
        Join the generated segments back info single audio file.
        """
        # Generate a file with each audio file in it. It doesn't
        # seem like there is a way to include each file as arguments
        # into ffmpeg for reasons...
        with open(self.ffmpeg_inp_file, "w") as stream_file:
            stream_file.write("\n".join("file '{}'".format(i) for i in files))

        cmd = ["ffmpeg", "-f", "concat", "-safe", "-0",
               "-i", self.ffmpeg_inp_file,
               "-c", "copy", "-y", "-f", "mp4", self.file_location ]

        # Probably should check for an error or something
        output = subprocess.check_output(cmd)

        # Delete the file parts and temp file
        for f in files:
            os.remove(f)
        os.remove(self.ffmpeg_inp_file)


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

