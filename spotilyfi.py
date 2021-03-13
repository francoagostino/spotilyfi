#!/usr/bin/env python
# coding: utf-8

import base64
import datetime
from urllib.parse import urlencode
import urllib.request

import requests
import re
from bs4 import BeautifulSoup



class spotilyfi(object):
    """
    - Specify client_id and client_secret as arguments to authenticate and use features.
    """

    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"


    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret


    def get_client_credentials(self):
        """
        Return a base64 encoded string.
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_id == None or client_secret == None:
            raise Exception("You must set client_id and client_secret")

        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()


    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {"Authorization": f"Basic {client_creds_b64}"}


    def get_token_data(self):
        return {"grant_type": "client_credentials"}


    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
        data = r.json()
        now = datetime.datetime.now()
        access_token = data["access_token"]
        self.access_token = access_token
        expires_in = data["expires_in"]
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True


    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token


    def get_resource_headers(self):
        access_token = self.get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        return headers


    def get_resource(self, lookup_id, resource_type="albums", version="v1"):
        """
        - Search Spotify by object id.
        - Possible resource type: album, artist, playlist, track, show or episode. Defaulted to album.
        - Current Spotify API version: v1. Can be specified if there's a version update.
        - Returns json with the specified id and resource type info.
        """
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_headers()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()


    def get_album(self, lookup_id):
        """
        - Search Spotify by ALBUM id.
        - Returns json with ALBUM info.
        """
        return self.get_resource(lookup_id, resource_type="albums")


    def get_artist(self, lookup_id):
        """
        - Search Spotify by ARTIST id.
        - Returns json with ARTIST info.
        """
        return self.get_resource(lookup_id, resource_type="artists")


    def get_audio_features(self, lookup_id):
        """
        - Search Spotify by track id.
        - Returns json with the track audio features.
        - The information provided is generated by Spotify.
        - It is advised to also use get_audio_analysis to retrieve confidence metrics.
        """
        return self.get_resource(lookup_id, resource_type="audio-features")


    def get_audio_analysis(self, lookup_id):
        """
        - Search Spotify by track id.
        - Returns json with the track audio analysis.
        - The information provided is generated by Spotify.
        """
        return self.get_resource(lookup_id, resource_type="audio-analysis")


    def base_search(self, query_params, search_type="artist"):
        """
        - Basic search feature for Spotify.
        - Query params can be specified as a dictionary with multiple entries
            {audio_feature : name}
        - Search type can be specified as: album , artist, playlist, track, show or episode. Defaulted to artist.
        - Returns json with the information specified in query params.
        """
        access_token = self.get_access_token()
        headers = self.get_resource_headers()
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()


    def search(self, query=None, operator=None, operator_query=None, search_type="artist"):
        """
        - Advanced search feature for Spotify.
        - Query can be specified as a dictionary with multiple entries
            {audio_feature : name}.
        - Operators NOT or OR can be used to refine the quey.
        - Operator query will be modified by the specified operators.
        - Returs json with the information specified in query.
        """
        if query is None:
            raise Exception("A query is required.")
        if isinstance(query, dict):
            query = " ".join([f"{k}:{v}" for k, v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator_query, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query, "type": search_type.lower()})
        return self.base_search(query_params)


    def album_list(self, artist):
        """
        - Search Spotify for the full album catalogue by the specified artist.
        - Returns a list with the album titles
        """
        albums = self.base_search({"artist": artist}, search_type="album")
        album_names = []
        for album in albums["albums"]["items"]:
            album_names.append(album["name"])
        return album_names


    def get_lyrics(self, artist, song_title):
        """
        - Search https://www.azlyrics.com/ for the specified song lyrics
        - Returns a string with the scrapped lyrics.
        - The string is not formated in order to retain it's html structure.

        --- SPECIAL WARNING ---
        - Overuse of this function will result in a temporary IP ban from AZlyrics.
        """
        artist = artist.lower()
        song_title = song_title.lower()
        # remove all except alphanumeric characters from artist and song_title
        artist = re.sub("[^A-Za-z0-9]+", "", artist)
        song_title = re.sub("[^A-Za-z0-9]+", "", song_title)
        # remove starting 'the' from artist e.g. the who -> who
        if artist.startswith("the"):
            artist = artist[3:]
        url = "http://azlyrics.com/lyrics/" + artist + "/" + song_title + ".html"

        try:
            content = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(content, "html.parser")
            lyrics = str(soup)
            # lyrics lies between up_partition and down_partition
            up_partition = "<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->"
            down_partition = "<!-- MxM banner -->"
            lyrics = lyrics.split(up_partition)[1]
            lyrics = lyrics.split(down_partition)[0]
            return lyrics
        except Exception as e:
            return "Exception occurred \n" + str(e)


    def tracks_info(self, artist, lyrics=False):
        """
        - Search Spotify for all albums and tracks by the specified artist.
            - Includes info present in the audio features and audio analysis.

        - Search https://www.azlyrics.com/ for the specified song lyrics.
            - The string is not formated in order to retain its html structure.
            - Lyrics function is off by default. Specify TRUE to activate.
            - Please read the SPECIAL WARNING section.

        - Returns json with information and lyrics found for each track.
        - Prints album name and track name to verify progress.

        --- SPECIAL CONSIDERATIONS ---
        - This functionction will return the parameters provided by Spotify that I found useful.
        - The whole parameter json can be achieved using the search function.

        --- SPECIAL WARNING ---
        - Overuse of this function will result in a temporary IP ban from AZlyrics.

        """
        tracks_info = []
        album_tracks = []
        album_names = self.album_list(artist)
        for album in album_names:
            print()
            print(f"\n ---{album}--- \n")
            tracks = self.base_search(
                {"artist": artist, "album": album}, search_type="track"
            )
            album_tracks[album] = tracks
            for track in album_tracks[album]["tracks"]["items"]:

                audio_features = self.get_audio_features(lookup_id=track["id"])
                audio_analysis = self.get_audio_analysis(lookup_id=track["id"])

                track_ = {
                    "artist": track["album"]["artists"][0]["name"],
                    "artist_id": track["album"]["artists"][0]["id"],
                    "album_name": album,
                    "album_id": track["album"]["id"],
                    "cover_art": track["album"]["images"][0]["url"],
                    "release_date": track["album"]["release_date"],
                    "total_tracks": track["album"]["total_tracks"],
                    "track_name": track["name"],
                    "track_id": track["id"],
                    "track_number": track["track_number"],
                    "disc_number": track["disc_number"],
                    "duration_ms": track["duration_ms"],
                    "popularity": track["popularity"],
                    "daceability": audio_features["danceability"],
                    "energy": audio_features["energy"],
                    "key": audio_features["key"],
                    "key_confidence": audio_analysis["track"]["key_confidence"],
                    "loudness": audio_features["loudness"],
                    "mode": audio_features["mode"],
                    "mode_confidence": audio_analysis["track"]["mode_confidence"],
                    "speechiness": audio_features["speechiness"],
                    "acousticness": audio_features["acousticness"],
                    "instrumentalness": audio_features["instrumentalness"],
                    "liveness": audio_features["liveness"],
                    "valence": audio_features["valence"],
                    "tempo": audio_features["tempo"],
                    "tempo_confidence": audio_analysis["track"]["tempo_confidence"],
                    "time_signature": audio_analysis["track"]["time_signature"],
                    "time_signature_confidence": audio_analysis["track"][
                        "time_signature_confidence"
                    ],
                }

                if lyrics == True:
                    lyrics_ = self.get_lyrics(artist, track["name"])
                    track_["lyrics"] = lyrics_

                print(f'{track_["track_number"]}- {track_["track_name"]}')
                tracks_info.append(track_)
        return tracks_info
