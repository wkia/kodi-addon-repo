# -*- coding: utf-8 -*-

import urllib
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin

from logging import log
from player import OpenlastPlayer
from util import build_url

__addon__ = xbmcaddon.Addon()
#__addonid__ = __addon__.getAddonInfo('id')
#__settings__ = xbmcaddon.Addon(id='xbmc-vk.svoka.com')
#__language__ = __settings__.getLocalizedString
#LANGUAGE     = __addon__.getLocalizedString
ADDONVERSION = __addon__.getAddonInfo('version')
#CWD = __addon__.getAddonInfo('path').decode("utf-8")

SESSION = 'openlast'

log('start -----------------------------------------------------', SESSION)
log('script version %s started' % ADDONVERSION, SESSION)

# xbmc.log(str(sys.argv))
addonUrl = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

#my_addon = xbmcaddon.Addon()
# lastfmUser = my_addon.getSetting('lastfm_username')

xbmcplugin.setContent(addon_handle, 'audio')




xbmc.log(str(args))
action = args.get('action', None)
folder = args.get('folder', None)

# xbmc.log('openlast: folder=' + str(folder)) #, xbmc.LOGDEBUG)
# xbmc.log('openlast: action=' + str(action)) #, xbmc.LOGDEBUG)

if folder is None:

    if '' != lastfmUser:
        url = build_url(addonUrl, {'folder': 'lastfm', 'username': lastfmUser})
        # xbmc.log(url)
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
        url = build_url(lastfmApi, {'method': 'user.getInfo', 'user': username,
                                    'format': 'json', 'api_key': lastfmApiKey})
        reply = urllib.urlopen(url)
        resp = json.load(reply)
        if "error" in resp:
            raise Exception("Error! DATA: " + str(resp))
        else:
            # xbmc.log(str(resp))
            pass

        img = resp['user']['image'][2]['#text']
        if '' == img:
            img = 'DefaultAudio.png'

    if action is None:
        url = build_url(addonUrl, {'folder': folder[0], 'action': 'lovedTracks', 'username': username})
        li = xbmcgui.ListItem('Listen to loved tracks', iconImage=img)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

    elif action[0] == 'lovedTracks':
        player = OpenlastPlayer()
        player.init(username)
        player.play()

        while(not xbmc.abortRequested and not player.stopped):
            xbmc.sleep(500)

        log('playback stopped', SESSION)

xbmcplugin.endOfDirectory(addon_handle)
log('end -----------------------------------------------------', SESSION)
