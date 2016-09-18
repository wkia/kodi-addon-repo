# -*- coding: utf-8 -*-

import xbmc

from history import History
from logging import log

SESSION = 'openlast'

class OpenlastPlayer(xbmc.Player):

    def __init__(self, *args):
        log('init player class', SESSION)
        xbmc.Player.__init__(self)
        self.history = History(10, 75)
        self.stopped = False
        pass

    def onPlayBackStarted(self):
        log('onPlayBackStarted', SESSION)
        # tags are not available instantly and we don't what to announce right
        # away as the user might be skipping through the songs
        xbmc.sleep(500)
        # get tags
        self._get_tags()
        pass

    def onPlayBackEnded(self):
        log('onPlayBackEnded', SESSION)
        pass

    def onPlayBackStopped(self):
        log('onPlayBackStopped', SESSION)
        self.stopped = True
        pass

    def _get_tags(self):
        # get track tags
        artist = self.getMusicInfoTag().getArtist().decode("utf-8")
        album = self.getMusicInfoTag().getAlbum().decode("utf-8")
        title = self.getMusicInfoTag().getTitle().decode("utf-8")
        duration = str(self.getMusicInfoTag().getDuration())
        # get duration from xbmc.Player if the MusicInfoTag duration is invalid
        if int(duration) <= 0:
            duration = str(int(self.getTotalTime()))
        track = str(self.getMusicInfoTag().getTrack())
        path = self.getPlayingFile().decode("utf-8")
        thumb = xbmc.getCacheThumbName(path)
        log('artist: ' + artist, SESSION)
        log('album: ' + album, SESSION)
        log('title: ' + title, SESSION)
        log('track: ' + str(track), SESSION)
        log('duration: ' + str(duration), SESSION)
        log('path: ' + path, SESSION)
        #log('local path: ' + user, SESSION)
        log('thumb: ' + thumb, SESSION)

        log('cover art: ' + str(xbmc.getInfoLabel('MusicPlayer.Cover')), SESSION)
        log('thumb art: ' + str(xbmc.getInfoLabel('Player.Art(thumb)')), SESSION)
        log('fan art: ' + str(xbmc.getInfoLabel('MusicPlayer.Property(Fanart_Image)')), SESSION)

