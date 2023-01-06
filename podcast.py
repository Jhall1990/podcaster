import os
import config
import episode
import feedparser

# Yeah this is kind of gross, but the podcast generator module that was in PyPi didn't
# work for me (wouldn't generate the correct format). Rather than spending a bunch of time
# creating an XML data structure I just did this, it works so far.
podcast_header = """<?xml version="1.0" encoding="UTF-8"?>
<!-- generator="podbean/5.5" -->
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/" xmlns:dc="http://purl.org/dc/elemen
ts/1.1/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:googleplay="http://www.google.com/schemas/play
-podcasts/1.0" xmlns:spotify="http://www.spotify.com/ns/rss" xmlns:media="http://search.yahoo.com/mrss/">

<channel>
    <title>{title}</title>
    <atom:link href="{url}" rel="self" type="application/rss+xml"/>
    <link>{url}</link>
    <description>{desc}</description>
    <pubDate>Thu, 31 May 2018 09:39:33 -0300</pubDate>
    <generator>me</generator>
    <language>en</language>
        <copyright>Copyright 2020 All rights reserved.</copyright>
    <category>{category}</category>
    <ttl>1440</ttl>
    <itunes:subtitle/>
    <itunes:summary>{desc}</itunes:summary>
    <itunes:author>me</itunes:author>
    <itunes:category text="{category}"/>
    <itunes:owner>
        <itunes:name>me</itunes:name>
        <itunes:email>{email}</itunes:email>
    </itunes:owner>
	<itunes:block>No</itunes:block>
	<itunes:explicit>no</itunes:explicit>
    <itunes:image href="https://upload.wikimedia.org/wikipedia/en/d/d3/Critical_Role_logo%2C_from_social_media_2020.jpg"/>
    <image>
        <url>https://upload.wikimedia.org/wikipedia/en/d/d3/Critical_Role_logo%2C_from_social_media_2020.jpg</url>
        <title>{title}</title>
        <link>{url}</link>
        <width>144</width>
        <height>144</height>
    </image>
""".format(**config.PODCAST_INFO)

podcast_item = """    <item>
      <title>{number} - {title}</title>
      <description><![CDATA[{title}]]></description>
      <guid isPermaLink="false">{url}</guid>
      <enclosure url="{url}" length="{length}" type="audio/mp4"/>
    </item>
"""

podcast_footer = """</channel>
<div id="saka-gui-root"/></rss>
"""


def get_episodes_in_rss():
    """
    Grabs all the episodes that already exist in the podcast and returns a list of
    episode objects. If the xml file doesn't exist an empty list is returned instead.
    """
    if os.path.exists(config.XML_LOCATION):
        feed = feedparser.parse(config.XML_LOCATION)
        episodes = [episode.Episode(i.summary, i.title.split("-")[0].strip(), "") for i in feed.entries]
        print("\n".join(["{} already in podcast...".format(i.title) for i in episodes]))
        return episodes
    else:
        return []


class PodcastCreator(object):
    """
    Handles generating a podcast rss (xml) file.
    """
    def __init__(self, episodes):
        self.episodes = episodes
        
        # Sort the episodes by their number, reversed. This
        # way new episodes appear first in you podcasting app
        # of choice.
        self.episodes.sort(key=lambda e: e.number, reverse=True)

    def create_podcast_xml(self):
        """
        Create the podcast xml (rss) by adding the header then
        an item for each episode followed by the footer.

        Then dump the created file in the XML_LOCATION specified in
        the config file.
        """
        print("Creating {}...".format(config.XML_LOCATION))

        xml = podcast_header
        
        for episode in self.episodes:
            args = {"number": episode.number,
                    "title": episode.title,
                    "url": episode.local_link,
                    "length": episode.size()}
            xml += podcast_item.format(**args)
        xml += podcast_footer

        with open(config.XML_LOCATION, "w") as xml_file:
            xml_file.write(xml)
