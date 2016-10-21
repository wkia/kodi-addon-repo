# -*- coding: utf-8 -*-

import sys
import urllib
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin

from player import OpenlastPlayer
from logging import log

#log(str(sys.argv))
username = sys.argv[1]

player = OpenlastPlayer()
success = player.init(username)

if not success:
    log('failed initializing addon')
    raise Exception("Failed initializing addon")

else:
    # Stop a player if any
    xbmc.Player().stop()
    xbmc.sleep(700)

    player.play()

    while(not xbmc.abortRequested and not player.stopped):
        xbmc.sleep(500)

    log('playback stopped')

