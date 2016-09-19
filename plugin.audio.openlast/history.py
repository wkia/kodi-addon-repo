# -*- coding: utf-8 -*-

class History:

    def __init__(self, maxArtistCount, maxTrackCount):
        self.maxArtistCount = maxArtistCount
        self.maxTrackCount = maxTrackCount
        self.artists = []
        self.tracks = []
        pass

    def _rescale(self, maxArtistCount, maxTrackCount):
        self.maxArtistCount = maxArtistCount
        self.maxTrackCount = maxTrackCount
        self._clean()
        pass

    def _clean(self):
        while len(self.artists) > self.maxArtistCount:
            self.artists.pop(0)
        while len(self.tracks) > self.maxTrackCount:
            self.tracks.pop(0)
        pass

    def addEntry(self, artist, track):
        self.artists.append(artist.lower())
        self.tracks.append(track.lower())
        self._clean()
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
