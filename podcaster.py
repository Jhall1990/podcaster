import config
import episode
import podcast


if __name__ == "__main__":
    # Get all episodes that match the provided regex.
    latest_episodes = episode.get_episodes(config.YOUTUBE_RSS, config.EPISODE_RE)

    # Open the current rss file and remove all episodes that have already been processes.
    episodes_in_pod = podcast.get_episodes_in_rss()

    # Download any remaining episodes.
    episodes_to_get = list(set(latest_episodes) - set(episodes_in_pod))
    episode.download_episodes(episodes_to_get)

    # Update the podcast rss feed.
    podcast = podcast.PodcastCreator(episodes_to_get + episodes_in_pod)
    podcast.create_podcast_xml()
