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
from util import strip_accents

lastfmApi = 'http://ws.audioscrobbler.com/2.0/'
lastfmApiKey = '47608ece2138b2edae9538f83f703457'  # TODO use Openlast key

MAX_ARTIST_COUNT = 10

class BasePlayer(xbmc.Player):

    WINDOW = 12006 # music visualization

    def __init__(self):
        log('creating player class')
        xbmc.Player.__init__(self)
        self.history = None
        self.tracks = None
        self.stopped = True
        self.dlgProgress = None
        pass

    def init(self):
        log('initializing player class')
        self.dlgProgress = xbmcgui.DialogProgress()
        self.dlgProgress.create('Openlast', 'Initializing addon...')
        self.dlgProgress.update(0)

        self.tracks = self.loadAllTracks()

        artistCount = len(self.tracks.keys())
        trackCount = len(self.tracks.values())
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

        if self.dlgProgress.iscanceled() or self.tracks is None:
            self.dlgProgress.close()
            self.dlgProgress = None
            return False

        return True

    def play(self):
        log('play')
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
        #log('onPlayBackStarted')
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
        log('onPlayBackStopped')
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
        #log('artist: ' + artist)
        #log('title: ' + title)
        #log('album: ' + album)
        #log('track: ' + str(track))
        #log('duration: ' + str(duration))
        #log('path: ' + path)
        #log('local path: ' + user)
        #log('thumb: ' + thumb)

        #log('cover art: ' + str(xbmc.getInfoLabel('MusicPlayer.Cover')))
        #log('thumb art: ' + str(xbmc.getInfoLabel('Player.Art(thumb)')))
        #log('fan art: ' + str(xbmc.getInfoLabel('MusicPlayer.Property(Fanart_Image)')))

        return [artist, title]

    def loadRecentTracks(self, username):
        url = build_url(lastfmApi, {'method': 'user.getrecenttracks', 'user': username,
                        'format': 'json', 'api_key': lastfmApiKey, 'limit': 500, 'page': 1})
        # xbmc.log(url)
        reply = urllib.urlopen(url)
        # xbmc.log(str(reply))
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            log('Successfully loaded recent tracks')

            if self.dlgProgress.iscanceled():
                return None
            self.dlgProgress.update(90)

            for t in resp['recenttracks']['track']:
                trackname = t['name'].lower()
                artistname = t['artist']['#text'].lower()
                #log(str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
                self.history.addEntry(artistname, trackname)

    def loadAllTracks(self):
        raise Exception("Should not be reached, use overridden method instead")
        pass

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
            trackname_stripped = strip_accents(trackname.strip().lower())
            for s in rpcresp['result']['songs']:
                if trackname_stripped == strip_accents(s['title'].strip().lower()):
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
            log(str(rpcresp))
            pass
        elif 'result' in rpcresp:
            found = 0 < int(rpcresp['result']['limits']['end'])
            pass

        if found:
            found = False
            artistname_stripped = strip_accents(artistname)
            for a in rpcresp['result']['artists']:
                if strip_accents(a['artist'].strip().lower()) == artistname_stripped:
                    #xbmc.log('Found artist: ' + str(artistname.encode('utf-8')))
                    found = True
                    # xbmc.log(str(rpcresp['result']))
                    for t in tracks:
                        item = self.findTrack(a['artist'], t)
                        if item is not None:
                            foundTrack = True
                            ret.append(item)

        if foundTrack:
            #log(len(ret))
            a = ret[len(ret) - 1]['artist'][0]
            if artistname.lower() <> a.lower():
                log("WARNING: artist name has some differencies: '" + str(artistname.encode('utf-8')) + "' --- '" + str(a.encode('utf-8')) + "'")

        if not found:
            log('NOT found artist: "' + str(artistname.encode('utf-8')) + '"')
            pass

        return ret

    def generateNextTrack(self):
        #log('Generating the next track')
        found = False
        item = None
        while not found:
            # Choose an artist
            a = random.randint(0, len(self.tracks) - 1)
            #log('Generated artist number %i' % a)
            artists = self.tracks.keys()
            artist = artists[a]
            #log('Generated artist "%s"' % artist)
            if self.history.isArtistRecentlyPlayed(artist):
                continue

            tryCount = 5
            while not found and 0 < tryCount:
                tryCount = tryCount - 1
                # Choose a track
                t = random.randint(0, len(self.tracks[artist]) - 1)
                #log('Generated track number %i' % t)
                res = self.findTracks(artist, [self.tracks[artist][t]])
                if len(res) == 0:
                    # Track not found
                    log('Track not found: %s - "%s", removing...' % (artist, self.tracks[artist][t]))
                    # Remove non-existent track from the list
                    del self.tracks[artist][t]
                    if 0 == len(self.tracks[artist]):
                        log('Artist "%s" has no more tracks, removing...' % artist)
                        del self.tracks[artist]
                        # Go to the another artist
                        tryCount = 0

                    # Rescale the history
                    artistCount = len(self.tracks.keys())
                    trackCount = len(self.tracks.values())
                    self.history.rescale(artistCount if artistCount < MAX_ARTIST_COUNT else MAX_ARTIST_COUNT, trackCount * 2 / 3)
                    # Try to choose another track of the same artist

                elif not self.history.isTrackRecentlyPlayed(self.tracks[artist][t]):
                    item = res[0]
                    log('The next track is: %s - "%s"' % (item['artist'][0], item['title']))
                    found = True

                else:
                    log('Track was recently played: %s - "%s", skipping...' % (artist, self.tracks[artist][t]))
                    # Try to choose another track of the same artist

        thumb = item['thumbnail']
        xlistitem = xbmcgui.ListItem(item['title'])
        xlistitem.setInfo("music", infoLabels={"Title": item['title']})
        xlistitem.setArt({'thumb': thumb})  # , 'fanart': thumb})

        return [item['file'], xlistitem]



class LovedTracksPlayer(BasePlayer):

    def __init__(self):
        log('creating player class')
        BasePlayer.__init__(self)
        self.username = ''
        pass

    def init(self, username):
        log('initializing player class, username=%s' % username)
        self.username = username
        return BasePlayer.init(self)

    def loadTracks(self, username, page):
        url = build_url(lastfmApi, {'method': 'user.getlovedtracks', 'user': username,
                        'format': 'json', 'api_key': lastfmApiKey, 'limit': 500, 'page': page})
        # xbmc.log(url)
        reply = urllib.urlopen(url)
        # xbmc.log(str(reply))
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            log('Successfully loaded loved tracks, page:' + str(page))

        return resp['lovedtracks']

    def loadAllTracks(self):
        #xbmc.executebuiltin('Notification(%s,%s)' % (SESSION, "Loading loved tracks..."))
        log('Loading loved tracks')
        loaded = False
        page = 1
        artists = {}
        while (True != loaded):
            resp = self.loadTracks(self.username, page)

            # for a in resp['@attr']:
            #    xbmc.log(str(a) + ': ' + resp['@attr'][str(a)])

            # Track the page number
            totalPages = int(resp['@attr']['totalPages'])
            page += 1
            loaded = (page > totalPages)

            if self.dlgProgress.iscanceled():
                return None
            self.dlgProgress.update(page * 50 / totalPages)

            for t in resp['track']:
                # xbmc.log(json.dumps(t).encode('utf-8'))
                if not self._preAddTrack(t):
                    page = totalPages
                    loaded = True
                    break
                trackname = t['name'].lower()
                artistname = t['artist']['name'].lower()
                # xbmc.log(str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
                # Put artists and tracks into the associative array
                if artistname in artists:
                    artists[artistname].append(trackname)
                else:
                    artists[artistname] = [trackname]

        return artists

    def _preAddTrack(self, track):
        return True



class TrackLibraryPlayer(LovedTracksPlayer):

    def __init__(self):
        log('creating player class')
        LovedTracksPlayer.__init__(self)
        pass

    def init(self, username, playcount):
        self.playcount = int(playcount) if 0 < int(playcount) else 1 # prevent dividing by zero
        self.avgPlaycount = 0
        return LovedTracksPlayer.init(self, username)

    def loadTracks(self, username, page):
        url = build_url(lastfmApi, {'method': 'user.gettoptracks', 'user': username,
                        'format': 'json', 'api_key': lastfmApiKey, 'limit': 500, 'page': page})
        # xbmc.log(url)
        reply = urllib.urlopen(url)
        # xbmc.log(str(reply))
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            log('Successfully loaded tracks, page:' + str(page))

        total = int(resp['toptracks']['@attr']['total'])
        self.avgPlaycount = self.playcount / total + 1

        return resp['toptracks']

    def _preAddTrack(self, track):
        if int(track['playcount']) < self.avgPlaycount:
            log('...the track\'s playcount exceeds the average: avg=' + str(self.avgPlaycount))
            return False
        return True

