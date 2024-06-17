import logging
from pathlib import Path
import git
import pandas as pd
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

repo_path = Path("./spotify-git-scraping/").resolve()


def iterate_file_versions(repo_path, filepath, ref="main"):
    repo = git.Repo(repo_path, odbt=git.GitDB)

    # pull latest changes
    try:
        repo.remotes[0].pull()
    except git.exc.GitCommandError as e:
        logger.error(f"Error pulling repo: {e}")

    commits = list(repo.iter_commits(ref))
    for commit in reversed(commits):
        try:
            for tree in commit.tree.trees:
                for blob in tree.blobs:
                    if filepath in blob.name:
                        yield blob.data_stream.read()
        except IndexError:
            pass


def extract_tracks_played(json_files):
    tracks_played = []
    for item in json_files:
        if item.get("items"):
            tracks_played.extend(item["items"])

    unique_tracks = {item["played_at"]: item for item in tracks_played}
    return list(unique_tracks.values())


def process_track(item):
    track_info = {
        "played_at": item["played_at"],
        "track_artists": " & ".join(
            artist["name"] for artist in item["track"]["artists"]
        ),
        "track_name": item["track"]["name"],
        "track_popularity": item["track"]["popularity"],
        "track_duration_ms": item["track"]["duration_ms"],
        "track_explicit": item["track"]["explicit"],
        "track_spotify_url": item["track"]["external_urls"]["spotify"],
        "track_preview_url": item["track"]["preview_url"],
        "track_track_number": item["track"]["track_number"],
        "track_uri": item["track"]["uri"],
        "track_disc_number": item["track"]["disc_number"],
        "track_href": item["track"]["href"],
        "track_id": item["track"]["id"],
        "track_is_local": item["track"]["is_local"],
        "track_artists_uris": " & ".join(
            f"{artist['name']}_{artist['uri']}" for artist in item["track"]["artists"]
        ),
    }
    for external_id, value in item["track"]["external_ids"].items():
        track_info[f"track_external_ids_{external_id}"] = value

    album = item["track"]["album"]
    album_artist = album["artists"][0]
    track_info.update(
        {
            "album_name": album["name"],
            "album_spotify_url": album["external_urls"]["spotify"],
            "album_release_date": album["release_date"],
            "album_uri": album["uri"],
            "album_id": album["id"],
            "album_href": album["href"],
            "album_release_date_precision": album["release_date_precision"],
            "album_type": album["album_type"],
            "album_total_tracks": album["total_tracks"],
            "album_artist_spotify_url": album_artist["external_urls"]["spotify"],
            "album_artist_href": album_artist["href"],
            "album_artist_id": album_artist["id"],
            "album_artist_name": album_artist["name"],
            "album_artist_uri": album_artist["uri"],
            "album_artists": " & ".join(artist["name"] for artist in album["artists"]),
        }
    )
    for image in album["images"]:
        height, width, url = image["height"], image["width"], image["url"]
        track_info[f"album_image_{height}x{width}_url"] = url

    return track_info


def main():
    json_files = [
        json.loads(file)
        for file in iterate_file_versions(repo_path, "recently_played.json")
    ]
    tracks_played = extract_tracks_played(json_files)
    tracks_holder = [process_track(item) for item in tracks_played]

    data = pd.DataFrame(tracks_holder).drop_duplicates().sort_values(by="played_at")
    data.to_csv("markdown/tracks.csv", index=False, encoding="utf-8")

    data["artists"] = data["track_artists"].str.split(" & ")
    data_exploded = data.explode("artists")
    data_exploded.to_csv("markdown/tracks_long.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
