import sys
import urllib
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

xbmc.log('openlast: start -----------------------------------------------------')

#__settings__ = xbmcaddon.Addon(id='xbmc-vk.svoka.com')
#__language__ = __settings__.getLocalizedString

xbmc.log(str(sys.argv))
addonUrl = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

lastfmApi = 'http://ws.audioscrobbler.com/2.0/'
lastfmApiKey = '47608ece2138b2edae9538f83f703457'  # TODO use Openlast key

lastfmAddon = xbmcaddon.Addon('service.scrobbler.lastfm')
my_addon = xbmcaddon.Addon()
# lastfmUser = my_addon.getSetting('lastfm_username')
lastfmUser = lastfmAddon.getSetting('lastfmuser')

xbmcplugin.setContent(addon_handle, 'audio')


def build_url(baseUrl, query):
    return baseUrl + '?' + urllib.urlencode(query)


def loadLovedTracks(username, page):
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
        xbmc.log('Successfully loaded loved tracks, page:' + str(page))

    return resp


def loadAllLovedTracks(username):
    xbmc.log('Loading loved tracks')
    loaded = False
    page = 1
    artists = {}
    while (True != loaded):
        resp = loadLovedTracks(username, page)

        # for a in resp['lovedtracks']['@attr']:
        #    xbmc.log(str(a) + ': ' + resp['lovedtracks']['@attr'][str(a)])

        # Track the page number
        totalPages = int(resp['lovedtracks']['@attr']['totalPages'])
        page += 1
        loaded = (page > totalPages)

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


def findTrack(artistname, trackname):
    # Find the song
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
                {"field": "title", "operator": "is", "value": trackname.encode('utf-8')}
            ]}
        }
    }
    rpcresp = xbmc.executeJSONRPC(json.dumps(req))
    # xbmc.log(str(rpcresp))
    rpcresp = json.loads(rpcresp)
    found = 0 < int(rpcresp['result']['limits']['end'])
    if found:
        #strInd = '+++ '
        #xbmc.log(str(rpcresp))
        return rpcresp['result']['songs'][0]
    else:
        #strInd = '    '
        xbmc.log('NOT found track ' + str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
        return None
    #xbmc.log(strInd + str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))


def findTracks(artistname, tracks):
    ret = []
    #req = {"jsonrpc": "2.0", "method": "JSONRPC.Version", "id": "1", "params": []}
    # Find artists with name starts with ...
    #chars0 = artistname[0].lower() + artistname[1].lower()
    #chars1 = artistname[0].upper() + artistname[1].lower()
    #chars2 = artistname[0].lower() + artistname[1].upper()
    #chars3 = artistname[0].upper() + artistname[1].upper()
    req = {
        "jsonrpc": "2.0",
        "method": "AudioLibrary.GetArtists",
        "id": "libSongs",
        "params": {
            "limits": {"start": 0, "end": 1000},
            "sort": {"order": "ascending", "method": "track", "ignorearticle": True},
            "filter": {"or": [
                {"field": "artist", "operator": "is", "value": artistname.encode('utf-8')}
                #{"field": "artist", "operator": "startswith", "value": chars0.encode('utf-8')},
                #{"field": "artist", "operator": "startswith", "value": chars1.encode('utf-8')},
                #{"field": "artist", "operator": "startswith", "value": chars2.encode('utf-8')},
                #{"field": "artist", "operator": "startswith", "value": chars3.encode('utf-8')},
            ]}
        }
    }
    # xbmc.log(json.dumps(req))
    rpcresp = xbmc.executeJSONRPC(json.dumps(req))
    # xbmc.log(str(rpcresp))
    rpcresp = json.loads(rpcresp)

    found = 0 < int(rpcresp['result']['limits']['end'])
    if found:
        found = False
        for art in rpcresp['result']['artists']:
            if art['artist'].strip().lower() == artistname:
                #xbmc.log('Found artist: ' + str(artistname.encode('utf-8')))
                found = True
                for t in tracks:
                    item = findTrack(artistname, t)
                    if item is not None:
                        ret.append(item)

    if not found:
        xbmc.log('NOT found artist: ' + str(artistname.encode('utf-8')))

    return ret


def generatePlaylist(username):
    xbmc.log('Generating a playlist')
    artists = loadAllLovedTracks(username)
    totalTracks = 0
    items = []
    for i, a in enumerate(artists):
        # xbmc.log(a)
        totalTracks += len(artists[a])
        items.extend(findTracks(a, artists[a]))

    xbmc.log("Found " + str(len(items)) + " tracks from " + str(totalTracks))

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    for i, item in enumerate(items):
        xbmc.log(str(item))
        image='DefaultFolder.png' #urllib.unquote(urlparse.urlparse(item['thumbnail']).netloc)
        xbmc.log(str(image)) #.encode('utf-8')))
        xlistitem = xbmcgui.ListItem(item['title'], iconImage=image, thumbnailImage=image)
        #xlistitem.setInfo("video", {"Title": title})
        playlist.add(item['file'], xlistitem)

    return playlist


class MyPlayer(xbmc.Player):

    def __init__(self, *args):
        xbmc.log('openlast: player created')
        xbmc.Player.__init__(self)

    def onPlayBackStarted(self):
        xbmc.log('openlast: player playback started')
        pass

    def onPlayBackEnded(self):
        xbmc.log('openlast: player playback ended')
        pass

    def onPlaybackStopped(self):
        xbmc.log('openlast: player playback stopped')
        pass

xbmc.log(str(args))
action = args.get('action', None)
folder = args.get('folder', None)

# xbmc.log('openlast: folder=' + str(folder)) #, xbmc.LOGDEBUG)
# xbmc.log('openlast: action=' + str(action)) #, xbmc.LOGDEBUG)

if folder is None:

    if '' != lastfmUser:
        url = build_url(addonUrl, {'folder': 'lastfm', 'username': lastfmUser})
        xbmc.log(url)
        li = xbmcgui.ListItem('Last.FM radio (' + lastfmUser + ')', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url(addonUrl, {'folder': 'lastfm'})
    li = xbmcgui.ListItem('Last.FM radio for user...', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

elif folder[0] == 'lastfm':

    username = ''
    if None != args.get('username'):
        username = args.get('username')[0]

    if username == '':
        user_keyboard = xbmc.Keyboard()
        user_keyboard.setHeading('Last.FM user name')  # __language__(30001))
        user_keyboard.setHiddenInput(False)
        user_keyboard.setDefault(lastfmUser)
        user_keyboard.doModal()
        if user_keyboard.isConfirmed():
            username = user_keyboard.getText()
        else:
            raise Exception("Login input was cancelled.")

    if action is None:
        url = build_url(lastfmApi, {
                        'method': 'user.getInfo', 'user': username, 'format': 'json', 'api_key': lastfmApiKey})
        reply = urllib.urlopen(url)
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            xbmc.log(str(resp))

        img = resp['user']['image'][2]['#text']
        if '' == img:
            img = 'DefaultAudio.png'

    if action is None:
        url = build_url(addonUrl, {'folder': folder[0], 'action': 'lovedTracks', 'username': username})
        li = xbmcgui.ListItem('Listen to loved tracks', iconImage=img)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    elif action[0] == 'lovedTracks':
        playlist = generatePlaylist(username)
        xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(playlist)
        #player = MyPlayer()
        # player.play()

        # while(not xbmc.abortRequested):
        #   xbmc.sleep(100)

        #xbmc.log('Abort requested')

xbmcplugin.endOfDirectory(addon_handle)
xbmc.log('openlast: end -----------------------------------------------------')
