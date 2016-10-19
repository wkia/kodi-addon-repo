# -*- coding: utf-8 -*-
#!/usr/bin/python

from urlparse import parse_qsl
import random
import sys
import xbmcaddon
import xbmcgui
import xbmcplugin

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

from logging import log
from util import build_url
from util import FileLock

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')
#__settings__ = xbmcaddon.Addon(id=__addonid__)
#__language__ = __settings__.getLocalizedString
#LANGUAGE     = __addon__.getLocalizedString
ADDONVERSION = __addon__.getAddonInfo('version')
#CWD = __addon__.getAddonInfo('path').decode("utf-8")

addonUrl = sys.argv[0]
addonHandle = int(sys.argv[1])

#log('start -----------------------------------------------------')
#log('script version %s started' % ADDONVERSION)
#log(str(sys.argv))


def getTvshows():
    req = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetTVShows",
        "id": 1,
        "params": {
            "properties": ["genre", "title", "originaltitle", "playcount", "file", "art", "thumbnail"],
            "limits": {"start": 0, "end": 1000},
            "sort": {"order": "ascending", "method": "title"},
        }
    }

    rpcresp = xbmc.executeJSONRPC(json.dumps(req))
    #log(str(rpcresp))
    rpcresp = json.loads(rpcresp)
    if 0 < int(rpcresp['result']['limits']['end']):
        return rpcresp['result']['tvshows']
    else:
        return []


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
    if 0 < int(rpcresp['result']['limits']['end']):
        return rpcresp['result']['episodes']
    else:
        return []


def getDuration(item):
    duration = 0
    if item["streamdetails"] is not None and item["streamdetails"]["video"] is not None and 0 < len(item["streamdetails"]["video"]):
        for e in item["streamdetails"]["video"]:
            duration = duration + e["duration"]
    else:
        duration = item["runtime"]

    return duration


def listTvshows():
    tvshows = getTvshows()
    listing = []
    for e in tvshows:
        #log(str(e))
        li = xbmcgui.ListItem(e['title'], iconImage='DefaultFolder.png')
        url = build_url(addonUrl, {'action': 'choosetime', 'tvshowid': e['tvshowid']})
        li.setInfo('video', {'title': e['title']})
        art = {}
        if 'thumbnail' in e:
            art['thumb'] = e['thumbnail']
        if 'art' in e:
            if 'banner' in e['art']:
                art['banner'] = e['art']['banner']
            if 'fanart' in e['art']:
                art['fanart'] = e['art']['fanart']
        li.setArt(art)
        isFolder = True
        listing.append((url, li, isFolder))

    xbmcplugin.addDirectoryItems(addonHandle, listing, len(listing))
    xbmcplugin.addSortMethod(addonHandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addonHandle)


def listItems(tvshowid):
    url = build_url(addonUrl, {'action': 'play', 'tvshowid': tvshowid, 'minutes': 30})
    li = xbmcgui.ListItem('30 minutes', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=False)
    url = build_url(addonUrl, {'action': 'play', 'tvshowid': tvshowid, 'minutes': 60})
    li = xbmcgui.ListItem('60 minutes', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=False)
    url = build_url(addonUrl, {'action': 'play', 'tvshowid': tvshowid, 'minutes': 90})
    li = xbmcgui.ListItem('90 minutes', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=False)
    url = build_url(addonUrl, {'action': 'play', 'tvshowid': tvshowid, 'minutes': 0})
    li = xbmcgui.ListItem('Custom length...', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=False)

    xbmcplugin.addSortMethod(addonHandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addonHandle)


def playVideo(tvshowid, minuteCount):
    filename = xbmc.translatePath("special://temp/" + __addonid__)
    #log('acquiring lock for %s...' % filename)
    lock = FileLock(filename)
    if not lock.acquire():
        log('lock for %s is busy' % filename)
        sys.exit(0)
    #log('acquired lock for %s' % filename)

    tvshowid = int(tvshowid)
    minuteCount = int(minuteCount)

    if 0 == minuteCount:
        user_keyboard = xbmc.Keyboard()
        user_keyboard.setHeading('Set custom playlist length in minutes')  # __language__(30001))
        user_keyboard.setHiddenInput(False)
        user_keyboard.setDefault("120")
        user_keyboard.doModal()
        if user_keyboard.isConfirmed():
            # int() throws an exception if falied
            minuteCount = int(user_keyboard.getText())
            if 0 >= minuteCount:
                raise Exception("Wrong length value")
        else:
            sys.exit(0)

    secondCount = minuteCount * 60
    random.seed()

    #log('--- stopping player')
    xbmc.Player().stop()
    xbmc.sleep(500)

    #log('--- creating playlist')
    episodes = getEpisodes(tvshowid)

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    xlistitem = xbmcgui.ListItem('video title')
    xlistitem.setInfo("video", infoLabels={"Title": 'video title'})
    #xlistitem.setProperty('IsPlayable', 'true')

    num = int(len(episodes) / 2)
    episodesRecent = episodes[num:]
    episodes = episodes[:num]

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

        #log("duration %d, seconds remain %d, %s" % (int(duration), int(secondCount), item['title']))
        if duration > secondCount and (duration - secondCount) > duration / 2:
            break

        xlistitem = xbmcgui.ListItem(item['title'])
        xlistitem.setInfo("video", infoLabels={"Title": item['title']})
        xlistitem.setArt({'thumb': item['thumbnail']})  # , 'fanart': thumb})
        playlist.add(item['file'], xlistitem)

        secondCount = secondCount - duration
        if secondCount <= 0:
            break

    #log('--- starting player')
    #playlist.shuffle()
    xbmc.Player().play(playlist)


def dispatch(param):
    params = dict(parse_qsl(param[1:]))
    if params:
        if params['action'] == 'choosetime':
            listItems(params['tvshowid'])
        elif params['action'] == 'play':
            playVideo(params['tvshowid'], params['minutes'])
    else:
        listTvshows()


if __name__ == '__main__':
    dispatch(sys.argv[2])

#log('end -----------------------------------------------------')
