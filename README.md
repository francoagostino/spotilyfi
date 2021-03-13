# **spotilyfi: Spotify API Client & Lyrics Finder**

## What is it?
**spotilyfi** is a script that leverages *Spotify's API* to retrieve information about albums, artists, playlists, tracks, shows and episodes. 

On top of this, it is capable to scrap *azlyrics.com* to obtain lyrics of a specified track (given that Spotify and AZlyrics utilize the same track name).

\

## How it is used?
To utilize **spotilyfi** you must create a Spotify developer user account [here](https://developer.spotify.com/) and create an APP to obtain your Client id and Client Secret credentials.

Once done you can use your credentials to authenticate, start the client and search:


```
# Your credentials
client_id = '***'
client_secret = '***'

# Start
sp = spotilyfi(client_id, client_secret)
```

Example:


```
# Get all tracks in an album
pos_rl = {
    'artist' : 'Pain of Salvation',
    'album': 'Remedy Lane'
}
rl_tracks = sp.search(pos_rl, search_type='track')
```

## WARNING
*AZlyrics* does not allow automated scrapnig of their website and will **temporally ban** your IP after abusing this feature.

The tracks_info function allows for autormated scraping of lyrics for multiple tracks. This feature can be activated by setting the lyrics argument equal to True.


```
tracks = sp.tracks_info(artist='Pain of Salvation', lyrics=True)
```

## Special Thanks
This script builds on [CodingEntrepreneurs](https://www.youtube.com/channel/UCWEHue8kksIaktO8KTTN_zg) tutorial on the Spotify API. Which can be found as **day 19** of their 30 days of Python series.
