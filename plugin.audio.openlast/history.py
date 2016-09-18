# -*- coding: utf-8 -*-

class History:

    def __init__(self, maxArtistCount, maxTrackCount):
        self.maxArtistCount = maxArtistCount
        self.maxTrackCount = maxTrackCount
        self.artists = []
        self.tracks = []
        pass

    def addEntry(self, artist, track):
        self.artists.append(artist.lower())
        if len(self.artists) > self.maxArtistCount:
            self.artists.pop(0)

        self.tracks.append(track.lower())
        if len(self.tracks) > self.maxTrackCount:
            self.tracks.pop(0)

        pass

    def isTrackRecentlyPlayed(self, track):
        try:
            self.tracks.index(track.lower())
        except ValueError:
            return False
        return True

    def isArtistRecentlyPlayed(self, artist):
        try:
            self.artists.index(artist.lower())
        except ValueError:
            return False
        return True
