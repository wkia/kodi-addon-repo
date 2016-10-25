# -*- coding: utf-8 -*-

import sys
import player

from logging import log

log(str(sys.argv))
action = sys.argv[1]

playerObj = None
if 'lovedTracks' == action:
    playerObj = player.LovedTracksPlayer()
    pass
elif 'topTracks' == action:
    playerObj = player.TrackLibraryPlayer()
    pass

log(str(sys.argv[2:]))
success = playerObj.init(*sys.argv[2:])

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

