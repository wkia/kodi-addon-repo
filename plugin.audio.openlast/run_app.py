# -*- coding: utf-8 -*-

import sys
import player

from logging import log

log(str(sys.argv))
log(str(sys.argv[1:]))

playerObj = player.LovedTracksPlayer()
success = playerObj.init(*sys.argv[1:])

if not success:
    log('failed initializing addon')
    raise Exception("Failed initializing addon")

else:
    # Stop a player if any
    xbmc.Player().stop()
    xbmc.sleep(700)

    playerObj.play()

    while(not xbmc.abortRequested and not playerObj.stopped):
        xbmc.sleep(500)

    log('playback stopped')

