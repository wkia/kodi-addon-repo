# -*- coding: utf-8 -*-

import os
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

from logging import log
from util import build_url

__addon__ = xbmcaddon.Addon()
#__addonid__ = __addon__.getAddonInfo('id')
#__settings__ = xbmcaddon.Addon(id='xbmc-vk.svoka.com')
#__language__ = __settings__.getLocalizedString
#LANGUAGE     = __addon__.getLocalizedString
ADDONVERSION = __addon__.getAddonInfo('version')
CWD = __addon__.getAddonInfo('path').decode("utf-8")

log('start -----------------------------------------------------')
log('script version %s started' % ADDONVERSION)

#xbmc.log(str(sys.argv))
addonUrl = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

#my_addon = xbmcaddon.Addon()
# lastfmUser = my_addon.getSetting('lastfm_username')

xbmcplugin.setContent(addon_handle, 'audio')

lastfmApi = 'http://ws.audioscrobbler.com/2.0/'
lastfmApiKey = '47608ece2138b2edae9538f83f703457'  # TODO use Openlast key

lastfmAddon = None
lastfmUser = ''
try:
    lastfmAddon = xbmcaddon.Addon('service.scrobbler.lastfm')
    lastfmUser = lastfmAddon.getSetting('lastfmuser')
except RuntimeError:
    pass

#xbmc.log(str(args))
action = args.get('action', None)
folder = args.get('folder', None)

#xbmc.log('openlast: folder=' + str(folder)) #, xbmc.LOGDEBUG)
#xbmc.log('openlast: action=' + str(action)) #, xbmc.LOGDEBUG)

if folder is None:

    if '' != lastfmUser:
        url = build_url(addonUrl, {'folder': 'lastfm', 'username': lastfmUser})
        # xbmc.log(url)
        li = xbmcgui.ListItem('Last.FM radio (' + lastfmUser + ')', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url(addonUrl, {'folder': 'lastfm'})
    li = xbmcgui.ListItem('Last.FM radio for user...', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif folder[0] == 'lastfm':

    username = ''
    if None != args.get('username'):
        username = args.get('username')[0]

    playcount = 0
    if None != args.get('playcount'):
        playcount = int(args.get('playcount')[0])

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
        url = build_url(lastfmApi, {'method': 'user.getInfo', 'user': username,
                                    'format': 'json', 'api_key': lastfmApiKey})
        reply = urllib.urlopen(url)
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            pass

        playcount = int(resp['user']['playcount'])
        img = resp['user']['image'][2]['#text']
        if '' == img:
            img = 'DefaultAudio.png'

        url = build_url(addonUrl, {'folder': folder[0], 'action': 'lovedTracks', 'username': username})
        li = xbmcgui.ListItem('Listen to loved tracks', iconImage=img)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

        url = build_url(addonUrl, {'folder': folder[0], 'action': 'topTracks', 'username': username, 'playcount': playcount})
        li = xbmcgui.ListItem('Listen to track library', iconImage=img)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

        url = build_url(addonUrl, {'folder': folder[0], 'action': 'topArtists', 'username': username, 'playcount': playcount})
        li = xbmcgui.ListItem('Listen to artist library', iconImage=img)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(addon_handle)

    elif action[0] == 'lovedTracks':
        script = os.path.join(CWD, "run_app.py")
        log('running script %s...' % script)
        xbmc.executebuiltin('XBMC.RunScript(%s, %s, %s)' % (script, action[0], username))

    elif action[0] == 'topTracks':
        script = os.path.join(CWD, "run_app.py")
        log('running script %s...' % script)
        xbmc.executebuiltin('XBMC.RunScript(%s, %s, %s, %s)' % (script, action[0], username, playcount))

    elif action[0] == 'topArtists':
        script = os.path.join(CWD, "run_app.py")
        log('running script %s...' % script)
        xbmc.executebuiltin('XBMC.RunScript(%s, %s, %s, %s)' % (script, action[0], username, playcount))

log('end -----------------------------------------------------')
