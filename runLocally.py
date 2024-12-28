#coding: utf-8
import json
import asyncio
from spotifyToYoutube import SpotifyToYoutube

def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description='Configuration arguments for the migration')

    parser.add_argument('--spotify-client-id', '-i', required=False, help='Spotify development app client id')
    parser.add_argument('--spotify-client-secret', '-s', required=False, help='Spotify development app client secret')
    parser.add_argument('--spotify-playlists', '-sp', required=False, help='Spotify playlists ids')
    parser.add_argument('--ytmusic-playlists', '-yp', required=False, help='Youtube music playlists names')
    parser.add_argument('--ytmusic-headers', '-yh', required=False, help='Youtube music headers')

    args = parser.parse_args()
    return args


# Opening our JSON configuration file (which has our tokens).
with open("config.json", encoding='utf-8-sig') as json_file:
    jsonConfig = json.load(json_file)

async def add_with_progress(ytmusic, track, target_playlist_id, task_index, total_tasks):
    # Add the track and print the progress after each task
    await spotifyToYoutube.async_add_to_playlist(ytmusic, track, target_playlist_id)
    remaining_tasks = total_tasks - (task_index + 1)
    print(f"Track {task_index + 1}/{total_tasks} added. {remaining_tasks} tracks left...")

async def main():
    args = parse_arguments()
    spotifyToYoutube = SpotifyToYoutube()

    sourcePlaylists = json.loads(args.spotify_playlists) if args.spotify_playlists != None else jsonConfig["spotify"]["playlists"]
    targetPlaylists = json.loads(args.ytmusic_playlists) if args.ytmusic_playlists != None else jsonConfig["google"]["playlists"]

    # Save the YouTube music headers to file if provided
    if args.ytmusic_headers:
        with open('ytmusic_headers.json', 'w', encoding='utf-8') as ytmusic_headers_file:
            json.dump(json.loads(args.ytmusic_headers), ytmusic_headers_file, ensure_ascii=False, indent=4)

    ytmusic = spotifyToYoutube.login_to_google('ytmusic_headers.json')

    if len(sourcePlaylists) != len(targetPlaylists):
        print("Please use the same number of Source and Target playlists")
    else:
        for index, playlist_url in enumerate(sourcePlaylists):
            print(f"Processing {playlist_url}...")
            print("Getting tracks...")

            tracks = spotifyToYoutube.get_tracks(
                playlist_url, 
                args.spotify_client_id or jsonConfig["spotify"]["client_id"], 
                args.spotify_client_secret or jsonConfig["spotify"]["client_secret"]
            )

            targetPlaylist = targetPlaylists[index]
            print(f"Target Playlist: {targetPlaylist}")

            # Create the target playlist on YouTube
            targetPlaylistId = ytmusic.create_playlist(targetPlaylist, targetPlaylist)

            # Asynchronously add tracks to the playlist with progress
            tasks = [
                add_with_progress(ytmusic, track, targetPlaylistId, i, len(tracks)) for i, track in enumerate(tracks)
            ]
            await asyncio.gather(*tasks)  # Run all tasks concurrently
            
            print(f"Migration for {targetPlaylist} finished!")

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
