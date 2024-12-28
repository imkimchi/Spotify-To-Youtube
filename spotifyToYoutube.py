#coding: utf-8

# Spotify library.
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# google library
from ytmusicapi import YTMusic
import requests
import traceback
import functools
import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

class SpotifyToYoutube():
    
    def __init__(self):
        self.search_cache = {}  # Cache for storing videoId lookups
    
    def login_to_google(self, ytmusic_headers):
        session = requests.Session()
        session.request = functools.partial(session.request, timeout=60)
        ytmusic = YTMusic(ytmusic_headers, requests_session=session)
        return ytmusic

    async def async_add_to_playlist(self, ytmusic, video_name, target_playlist):
        # If video is already in cache, skip the search
        if video_name in self.search_cache:
            video_id = self.search_cache[video_name]
        else:
            search_results = ytmusic.search(video_name, "songs") or ytmusic.search(video_name, "videos")
            if len(search_results) > 0:
                video_id = search_results[0]['videoId']
                # Cache the result to avoid re-searching in the future
                self.search_cache[video_name] = video_id
            else:
                video_id = None
        
        if video_id:
            retries = 3
            while retries != 0:
                try:
                    await asyncio.to_thread(ytmusic.add_playlist_items, target_playlist, [video_id])
                    retries = 0
                except Exception as e:
                    print("An exception occurred:", e)
                    retries -= 1

    async def add_tracks_concurrently(self, ytmusic, tracks, target_playlist):
        # Run add_to_playlist for each track concurrently
        tasks = [self.async_add_to_playlist(ytmusic, track, target_playlist) for track in tracks]
        await asyncio.gather(*tasks)

    def get_tracks(self, playlist_url, spotify_client_id, spotify_client_secret):
        # Creating and authenticating our Spotify app.
        client_credentials_manager = SpotifyClientCredentials(spotify_client_id, spotify_client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        track_list = []

        # Getting a playlist.
        results = spotify.user_playlist_tracks(user="", playlist_id=playlist_url)
        tracks = results['items']
        while results['next']:
            results = spotify.next(results)
            tracks.extend(results['items'])

        # For each track in the playlist.
        for track in tracks:
            try:
                if(track == None or track["track"] == None):
                    print(track)
                elif(track["track"]["artists"] == None):
                    track_list.append(track["track"]["name"])
                # In case there's only one artist.
                elif (len(track["track"]["artists"]) == 1):
                    track_list.append(track["track"]["name"] + " - " + track["track"]["artists"][0]["name"])
                # In case there's more than one artist.
                else:
                    name_string = ""
                    for index, artist in enumerate(track["track"]["artists"]):
                        name_string += (artist["name"])
                        if (len(track["track"]["artists"]) - 1 != index):
                            name_string += ", "
                    track_list.append(track["track"]["name"] + " - " + name_string)
            except Exception as e:
                print("An exception occurred:", e)
                
        return track_list

# Main function
async def main():
    spotifyToYoutube = SpotifyToYoutube()

    # Replace with your playlist details
    sourcePlaylists = ["your_spotify_playlist_id"]
    targetPlaylists = ["your_youtube_playlist_name"]
    
    ytmusic_headers = "path_to_your_ytmusic_headers.json"
    ytmusic = spotifyToYoutube.login_to_google(ytmusic_headers)

    # Assume you already have the Spotify playlist tracks
    for index, playlist_url in enumerate(sourcePlaylists):
        print(f"Getting tracks for {playlist_url}...")
        tracks = spotifyToYoutube.get_tracks(playlist_url, "spotify_client_id", "spotify_client_secret")
        targetPlaylist = targetPlaylists[index]

        targetPlaylistId = ytmusic.create_playlist(targetPlaylist, targetPlaylist)

        # Add tracks to playlist concurrently
        await spotifyToYoutube.add_tracks_concurrently(ytmusic, tracks, targetPlaylistId)
        
        print("Migration finished!")

if __name__ == "__main__":
    asyncio.run(main())
