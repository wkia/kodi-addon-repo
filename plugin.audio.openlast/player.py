# -*- coding: utf-8 -*-

import random
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

from history import History
from logging import log
from util import build_url

SESSION = 'openlast'

lastfmApi = 'http://ws.audioscrobbler.com/2.0/'
lastfmApiKey = '47608ece2138b2edae9538f83f703457'  # TODO use Openlast key

MAX_ARTIST_COUNT = 10

class OpenlastPlayer(xbmc.Player):

    WINDOW = 12006 # music visualization

    def __init__(self):
        log('creating player class', SESSION)
        xbmc.Player.__init__(self)
        self.history = None
        self.lovedTracks = None
        self.stopped = True
        self.username = ''
        self.dlgProgress = None
        pass

    def init(self, username):
        log('initializing player class, username=%s' % username, SESSION)
        self.dlgProgress = xbmcgui.DialogProgress()
        self.dlgProgress.create(SESSION, 'Initializing addon...')
        self.dlgProgress.update(0)

        self.username = username
        self.lovedTracks = self.loadAllLovedTracks(self.username)

        artistCount = len(self.lovedTracks.keys())
        trackCount = len(self.lovedTracks.values())
        self.history = History(artistCount if artistCount < MAX_ARTIST_COUNT else MAX_ARTIST_COUNT, trackCount * 2 / 3)
        random.seed()

        lastfmUser = ''
        try:
            lastfmAddon = xbmcaddon.Addon('service.scrobbler.lastfm')
            lastfmUser = lastfmAddon.getSetting('lastfmuser')
        except RuntimeError:
            pass
        if 0 < len(lastfmUser):
            self.loadRecentTracks(lastfmUser)

        if self.dlgProgress.iscanceled() or self.lovedTracks is None:
            self.dlgProgress.close()
            self.dlgProgress = None
            return False

        return True

    def play(self):
        log('play', SESSION)
        self.stopped = False
        nextItem = self.generateNextTrack()
        self.dlgProgress.update(100)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        playlist.add(nextItem[0], nextItem[1])
        self.dlgProgress.close()
        xbmc.Player.play(self, playlist)
        xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW,))
        pass

    def onPlayBackStarted(self):
        log('onPlayBackStarted', SESSION)
        # tags are not available instantly and we don't what to announce right
        # away as the user might be skipping through the songs
        xbmc.sleep(500)

        # get tags
        entry = self._get_tags()
        self.history.addEntry(entry[0], entry[1])

        # choose the next track
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        if playlist.getposition() + 1 == playlist.size():
            nextItem = self.generateNextTrack()
            playlist.add(nextItem[0], nextItem[1])
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
        log('title: ' + title, SESSION)
        log('album: ' + album, SESSION)
        #log('track: ' + str(track), SESSION)
        #log('duration: ' + str(duration), SESSION)
        #log('path: ' + path, SESSION)
        #log('local path: ' + user, SESSION)
        #log('thumb: ' + thumb, SESSION)

        #log('cover art: ' + str(xbmc.getInfoLabel('MusicPlayer.Cover')), SESSION)
        #log('thumb art: ' + str(xbmc.getInfoLabel('Player.Art(thumb)')), SESSION)
        #log('fan art: ' + str(xbmc.getInfoLabel('MusicPlayer.Property(Fanart_Image)')), SESSION)

        return [artist, title]

    def loadLovedTracks(self, username, page):
        url = build_url(lastfmApi, {'method': 'user.getlovedtracks', 'user': username,
                        'format': 'json', 'api_key': lastfmApiKey, 'limit': 200, 'page': page})
        # xbmc.log(url)
        reply = urllib.urlopen(url)
        # xbmc.log(str(reply))
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            log('Successfully loaded loved tracks, page:' + str(page), SESSION)

        return resp

    def loadRecentTracks(self, username):
        url = build_url(lastfmApi, {'method': 'user.getrecenttracks', 'user': username,
                        'format': 'json', 'api_key': lastfmApiKey, 'limit': 200, 'page': 1})
        # xbmc.log(url)
        reply = urllib.urlopen(url)
        # xbmc.log(str(reply))
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            log('Successfully loaded recent tracks', SESSION)

            if self.dlgProgress.iscanceled():
                return None
            self.dlgProgress.update(90)

            for t in resp['recenttracks']['track']:
                trackname = t['name'].lower()
                artistname = t['artist']['#text'].lower()
                #log(str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')), SESSION)
                self.history.addEntry(artistname, trackname)

    def loadAllLovedTracks(self, username):
        #xbmc.executebuiltin('Notification(%s,%s)' % (SESSION, "Loading loved tracks..."))
        log('Loading loved tracks', SESSION)
        loaded = False
        page = 1
        artists = {}
        while (True != loaded):
            resp = self.loadLovedTracks(username, page)

            # for a in resp['lovedtracks']['@attr']:
            #    xbmc.log(str(a) + ': ' + resp['lovedtracks']['@attr'][str(a)])

            # Track the page number
            totalPages = int(resp['lovedtracks']['@attr']['totalPages'])
            page += 1
            loaded = (page > totalPages)

            if self.dlgProgress.iscanceled():
                return None
            self.dlgProgress.update(page * 100 / (totalPages + 1))

            for t in resp['lovedtracks']['track']:
                # xbmc.log(json.dumps(t).encode('utf-8'))
                trackname = t['name'].lower()
                artistname = t['artist']['name'].lower()
                # xbmc.log(str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
                # Put artists and tracks into the associative array
                if artistname in artists:
                    artists[artistname].append(trackname)
                else:
                    artists[artistname] = [trackname]

        return artists


    def findTrack(self, artistname, trackname):
        # Find the song
        chars0 = trackname[0].lower() + trackname[1].lower()
        chars1 = trackname[0].upper() + trackname[1].lower()
        chars2 = trackname[0].lower() + trackname[1].upper()
        chars3 = trackname[0].upper() + trackname[1].upper()
        req = {
            "jsonrpc": "2.0",
            "method": "AudioLibrary.GetSongs",
            "id": "libSongs",
            "params": {
                "properties": ["artist", "duration", "album", "title", "file", "thumbnail", "fanart"],
                "limits": {"start": 0, "end": 1000},
                "sort": {"order": "ascending", "method": "track", "ignorearticle": True},
                "filter": {"and": [
                    {"field": "artist", "operator": "is", "value": artistname.encode('utf-8')},
                    {"or": [
                        #{"field": "title", "operator": "is", "value": trackname.lower().encode('utf-8')}
                        {"field": "title", "operator": "startswith", "value": chars0.encode('utf-8')},
                        {"field": "title", "operator": "startswith", "value": chars1.encode('utf-8')},
                        {"field": "title", "operator": "startswith", "value": chars2.encode('utf-8')},
                        {"field": "title", "operator": "startswith", "value": chars3.encode('utf-8')},
                    ]}
                ]}
            }
        }

        rpcresp = xbmc.executeJSONRPC(json.dumps(req))
        # xbmc.log(str(rpcresp))
        rpcresp = json.loads(rpcresp)
        found = 0 < int(rpcresp['result']['limits']['end'])
        ret = None
        #strInd = '    '
        if found:
            # xbmc.log(str(rpcresp))
            for s in rpcresp['result']['songs']:
                if trackname.lower() == s['title'].lower():
                    ret = s
                    break
            #if artistname.lower() <> ret['artist'][0].lower() or trackname.lower() <> ret['title'].lower():
            #if ret is not None:
            #    strInd = '+++ '
            #    xbmc.log(strInd + str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
            #    xbmc.log('    ' + str(ret['artist'][0].encode('utf-8')) + " -- " + str(ret['title'].encode('utf-8')))
        #else:
            #xbmc.log('NOT found track ' + str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))

        #xbmc.log(strInd + str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
        return ret


    def findTracks(self, artistname, tracks):
        ret = []
        # Find artists with name starts with ...
        chars0 = artistname[0].lower() + artistname[1].lower()
        chars1 = artistname[0].upper() + artistname[1].lower()
        chars2 = artistname[0].lower() + artistname[1].upper()
        chars3 = artistname[0].upper() + artistname[1].upper()
        req = {
            "jsonrpc": "2.0",
            "method": "AudioLibrary.GetArtists",
            "id": "libSongs",
            "params": {
                #"properties": ["thumbnail", "fanart"],
                "limits": {"start": 0, "end": 1000},
                "sort": {"order": "ascending", "method": "track", "ignorearticle": True},
                "filter": {"or": [
                    #{"field": "artist", "operator": "is", "value": artistname.encode('utf-8')}
                    {"field": "artist", "operator": "startswith", "value": chars0.encode('utf-8')},
                    {"field": "artist", "operator": "startswith", "value": chars1.encode('utf-8')},
                    {"field": "artist", "operator": "startswith", "value": chars2.encode('utf-8')},
                    {"field": "artist", "operator": "startswith", "value": chars3.encode('utf-8')},
                ]}
            }
        }
        # xbmc.log(json.dumps(req))
        rpcresp = xbmc.executeJSONRPC(json.dumps(req))
        # xbmc.log(str(rpcresp))
        rpcresp = json.loads(rpcresp)

        found = False
        foundTrack = False
        if 'error' in rpcresp:
            log(str(rpcresp), SESSION)
            pass
        elif 'result' in rpcresp:
            found = 0 < int(rpcresp['result']['limits']['end'])
            pass

        if found:
            found = False
            for a in rpcresp['result']['artists']:
                if a['artist'].strip().lower() == artistname:
                    #xbmc.log('Found artist: ' + str(artistname.encode('utf-8')))
                    found = True
                    # xbmc.log(str(rpcresp['result']))
                    for t in tracks:
                        item = self.findTrack(a['artist'], t)
                        if item is not None:
                            foundTrack = True
                            ret.append(item)

        if foundTrack:
            #log(len(ret), SESSION)
            a = ret[len(ret) - 1]['artist'][0]
            if artistname.lower() <> a.lower():
                log("WARNING: artist name has leading spaces: '" + str(a.encode('utf-8')) + "'", SESSION)

        if not found:
            log('NOT found artist: "' + str(artistname.encode('utf-8')) + '"', SESSION)
            pass

        return ret


    def generatePlaylist(self, username):
        artists = self.loadAllLovedTracks(username)
        #xbmc.executebuiltin('Notification(%s,%s)' % (SESSION, "Finding local songs..."))
        log('Finding local songs...', SESSION)
        totalTracks = 0
        items = []
        for i, a in enumerate(artists):
            # xbmc.log(a)
            totalTracks += len(artists[a])
            items.extend(self.findTracks(a, artists[a]))

        log("Found " + str(len(items)) + " tracks from " + str(totalTracks), SESSION)

        #xbmc.executebuiltin('Notification(%s,%s)' % (SESSION, "Generating playlist..."))
        log('Generating a playlist', SESSION)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        for i, item in enumerate(items):
            # xbmc.log(str(item))
            thumb = item['thumbnail']
            # xbmc.log(str(thumb).encode('utf-8'))
            xlistitem = xbmcgui.ListItem(item['title'])
            xlistitem.setInfo("music", infoLabels={"Title": item['title']})
            xlistitem.setArt({'thumb': thumb})  # , 'fanart': thumb})
            playlist.add(item['file'], xlistitem)
            break

        return playlist

    def generateNextTrack(self):
        log('Generating the next track', SESSION)
        found = False
        item = None
        while not found:
            # Choose an artist
            a = random.randint(0, len(self.lovedTracks) - 1)
            #log('Generated artist number %i' % a, SESSION)
            artists = self.lovedTracks.keys()
            artist = artists[a]
            #log('Generated artist "%s"' % artist, SESSION)
            if self.history.isArtistRecentlyPlayed(artist):
                continue

            tryCount = 5
            while not found and 0 < tryCount:
                # Choose a track
                t = random.randint(0, len(self.lovedTracks[artist]) - 1)
                #log('Generated track number %i' % t, SESSION)
                res = self.findTracks(artist, [self.lovedTracks[artist][t]])
                if len(res) == 0:
                    # Track not found
                    log('Track not found: %s - "%s", removing...' % (artist, self.lovedTracks[artist][t]), SESSION)
                    # Remove non-existent track from the list
                    del self.lovedTracks[artist][t]
                    if 0 == len(self.lovedTracks[artist]):
                        log('Artist "%s" has no more tracks, removing...' % artist, SESSION)
                        del self.lovedTracks[artist]
                        # Go to the another artist
                        tryCount = 0

                    # Rescale the history
                    artistCount = len(self.lovedTracks.keys())
                    trackCount = len(self.lovedTracks.values())
                    self.history.rescale(artistCount if artistCount < MAX_ARTIST_COUNT else MAX_ARTIST_COUNT, trackCount * 2 / 3)

                    # Try to choose another track of the same artist
                    tryCount = tryCount - 1

                elif not self.history.isTrackRecentlyPlayed(self.lovedTracks[artist][t]):
                    item = res[0]
                    log('The next track is: %s - "%s"' % (item['artist'][0], item['title']), SESSION)
                    found = True

        thumb = item['thumbnail']
        xlistitem = xbmcgui.ListItem(item['title'])
        xlistitem.setInfo("music", infoLabels={"Title": item['title']})
        xlistitem.setArt({'thumb': thumb})  # , 'fanart': thumb})

        return [item['file'], xlistitem]
