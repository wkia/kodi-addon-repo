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
        url = build_url(lastfmApi, {'method': 'user.getlovedtracks', 'user': lastfmUser,
                                    'format': 'json', 'api_key': lastfmApiKey, 'limit': 200})
        xbmc.log(url)
        reply = urllib.urlopen(url)
        xbmc.log(str(reply))
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            xbmc.log(str(resp))

        for a in resp['lovedtracks']['@attr']:
            xbmc.log(str(a) + ': ' + resp['lovedtracks']['@attr'][str(a)])
        for t in resp['lovedtracks']['track']:
            # xbmc.log(json.dumps(t).encode('utf-8'))
            trackname = t['name']
            artistname = t['artist']['name']
            # xbmc.log(str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))
            req = {"jsonrpc": "2.0", "method": "JSONRPC.Version", "id": "1", "params": []}

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
                    "limits": {"start": 0, "end": 1000},
                    "sort": {"order": "ascending", "method": "track", "ignorearticle": True},
                    "filter": {"or": [
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
            found = 0 < int(rpcresp['result']['limits']['end'])
            if found:
                for art in rpcresp['result']['artists']:
                    if art['artist'].strip().lower() == artistname.lower():
                        # Found the artist
                        # xbmc.log(str(art['artist'].encode('utf-8')))

                        # Find the song
                        req = {
                            "jsonrpc": "2.0",
                            "method": "AudioLibrary.GetSongs",
                            "id": "libSongs",
                            "params": {
                                "properties": ["artist", "duration", "album", "title"],
                                "limits": {"start": 0, "end": 1000},
                                "sort": {"order": "ascending", "method": "track", "ignorearticle": True},
                                "filter": {"and": [
                                    {"field": "artist", "operator": "is", "value": art['artist'].encode('utf-8')},
                                    {"field": "title", "operator": "is", "value": trackname.encode('utf-8')}
                                ]}
                            }
                        }
                        rpcresp2 = xbmc.executeJSONRPC(json.dumps(req))
                        # xbmc.log(str(rpcresp2))
                        rpcresp2 = json.loads(rpcresp2)
                        found2 = 0 < int(rpcresp2['result']['limits']['end'])
                        if found2:
                            strInd = '+++ '
                        else:
                            strInd = '    '
                        xbmc.log(strInd + str(artistname.encode('utf-8')) + " -- " + str(trackname.encode('utf-8')))

        #player = MyPlayer()
        # player.play()

        # while(not xbmc.abortRequested):
        #    xbmc.sleep(100)


xbmcplugin.endOfDirectory(addon_handle)
