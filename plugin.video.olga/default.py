# -*- coding: utf-8 -*-

import random
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

from logging import log
from util import build_url

__addon__ = xbmcaddon.Addon()
#__addonid__ = __addon__.getAddonInfo('id')
#__settings__ = xbmcaddon.Addon(id=__addonid__)
#__language__ = __settings__.getLocalizedString
#LANGUAGE     = __addon__.getLocalizedString
ADDONVERSION = __addon__.getAddonInfo('version')
#CWD = __addon__.getAddonInfo('path').decode("utf-8")

SESSION = 'olga'

log('start -----------------------------------------------------', SESSION)
log('script version %s started' % ADDONVERSION, SESSION)

#xbmc.log(str(sys.argv))
addonUrl = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
#xbmc.log(str(args))

xbmcplugin.setContent(addon_handle, 'video')

minuteCount = args.get('minutes', None)
tvshowid = args.get('tvshowid', None)

def getTvshows():
    req = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetTVShows",
        "id": 1,
        "params": {
            "properties": ["genre", "title", "originaltitle", "playcount", "file"],
            "limits": {"start": 0, "end": 1000},
            "sort": {"order": "ascending", "method": "title"},
        }
    }

    rpcresp = xbmc.executeJSONRPC(json.dumps(req))
    #xbmc.log(str(rpcresp))
    rpcresp = json.loads(rpcresp)
    return rpcresp


def getEpisodes(tvshowid):
    req = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetEpisodes",
        "id": 1,
        "params": {
            "tvshowid": tvshowid,
            #"season": -1,
            "properties": ["title", "runtime", "file", "lastplayed", "thumbnail", "streamdetails"],
            "limits": {"start": 0, "end": 1000},
            "sort": {"order": "ascending", "method": "lastplayed"},
        }
    }

    rpcresp = xbmc.executeJSONRPC(json.dumps(req))
    #xbmc.log(str(rpcresp))
    rpcresp = json.loads(rpcresp)
    return rpcresp


def getDuration(item):
    duration = 0
    if item["streamdetails"] is not None and item["streamdetails"]["video"] is not None and 0 < len(item["streamdetails"]["video"]):
        for e in item["streamdetails"]["video"]:
            duration = duration + e["duration"]
    else:
        duration = item["runtime"]

    return duration


if tvshowid is None:

    tvshows = getTvshows()
    found = 0 < int(tvshows['result']['limits']['end'])
    if found :
        for e in tvshows['result']['tvshows']:
            url = build_url(addonUrl, {'tvshowid': e['tvshowid']})
            li = xbmcgui.ListItem(e['title'], iconImage='DefaultFolder.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

elif minuteCount is None:

    tvshowid = int(tvshowid[0])

    url = build_url(addonUrl, {'tvshowid': tvshowid, 'minutes': 30})
    li = xbmcgui.ListItem('30 minutes', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    url = build_url(addonUrl, {'tvshowid': tvshowid, 'minutes': 60})
    li = xbmcgui.ListItem('60 minutes', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    url = build_url(addonUrl, {'tvshowid': tvshowid, 'minutes': 90})
    li = xbmcgui.ListItem('90 minutes', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    url = build_url(addonUrl, {'tvshowid': tvshowid, 'minutes': 0})
    li = xbmcgui.ListItem('Custom length...', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

else:

    tvshowid = int(tvshowid[0])
    minuteCount = int(minuteCount[0])

    if 0 == minuteCount:
        user_keyboard = xbmc.Keyboard()
        user_keyboard.setHeading('Set custom playlist length in minutes')  # __language__(30001))
        user_keyboard.setHiddenInput(False)
        user_keyboard.setDefault("60")
        user_keyboard.doModal()
        if user_keyboard.isConfirmed():
            # int() throws an exception if falied
            minuteCount = int(user_keyboard.getText())
            if 0 >= minuteCount:
                raise Exception("Wrong length value")
        else:
            raise Exception("Login input was cancelled.")

    # Generate random playlist
    xbmc.Player().stop()
    xbmc.sleep(500)
    random.seed()
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    secondCount = minuteCount * 60
    #minRuntime = 0
    #maxRuntime = 0
    #episodeCount = 0

    episodes = getEpisodes(tvshowid)
    found = 0 < int(episodes['result']['limits']['end'])
    if found :
        episodes = episodes['result']['episodes']
        num = int(len(episodes) / 2)
        episodesRecent = episodes[num:]
        episodes = episodes[:num]
        #minRuntime = episodes[0]['runtime']
        #maxRuntime = episodes[-1]['runtime']

        while 0 < len(episodes):
            n = random.randint(0, len(episodes) - 1)
            item = episodes.pop(n)
            if 0 == len(episodes) and 0 < len(episodesRecent):
                num = int(len(episodesRecent)/2 + 1)
                episodes = episodesRecent[:num]
                episodesRecent = episodesRecent[num:]

            #xbmc.log(str(item))
            duration = getDuration(item)
            if 0 == duration:
                continue
            secondCount = secondCount - duration
            if secondCount <= 0 or secondCount < duration / 2:
                break

            xlistitem = xbmcgui.ListItem(item['title'])
            xlistitem.setInfo("video", infoLabels={"Title": item['title']})
            xlistitem.setArt({'thumb': item['thumbnail']})  # , 'fanart': thumb})
            playlist.add(item['file'], xlistitem)

    else:
        # No series found
        raise Exception("No series found")

    #xbmc.executebuiltin("ActivateWindow(%d)" % (10000,))
    playlist.shuffle()
    xbmc.Player().play(playlist)


xbmcplugin.endOfDirectory(addon_handle)
log('end -----------------------------------------------------', SESSION)
