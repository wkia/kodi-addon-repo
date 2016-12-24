# -*- coding: utf-8 -*-

import errno
import os
import re
import shutil
import sys
import player
import xbmcgui

from logging import log
from util import strip_accents

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    ret = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    ret = unicode(re.sub('[^\w\s-]', '', ret).strip().lower())
    ret = unicode(re.sub('[-\s]+', '-', ret))
    return ret

log(str(sys.argv))
action = sys.argv[1]

playerObj = None
if 'lovedTracks' == action:
    playerObj = player.LovedTracksPlayer()
    pass
elif 'topTracks' == action:
    playerObj = player.TrackLibraryPlayer()
    pass
elif 'topArtists' == action:
    playerObj = player.ArtistLibraryPlayer()
    pass
elif 'syncLibrary' == action:
    dialog = xbmcgui.Dialog()
    path = dialog.browseSingle(3, 'Select folder', 'files')
    log('Path = "%s"' % path)

    if '' != path:
      playerObj = player.LovedTracksPlayer()
      playerObj.init(*sys.argv[2:])
      log('Artist count = %d' % len(playerObj.tracks.keys()))
      for a in playerObj.tracks.keys():
          aPath = os.path.join(path, slugify(strip_accents(a.strip())))
          for t in playerObj.tracks[a]:
              #log('# %s' % a)
              track = playerObj.findTrack(a, t)
              if None != track:
                  tPath = os.path.join(aPath, slugify(strip_accents(track['album'].strip().lower())))
                  base, extension = os.path.splitext(track['file'])
                  #log('Track: base = %s, extension = %s' % (base, extension))
                  tFile = os.path.join(tPath, slugify(str(track['track']).zfill(3) + '-' + strip_accents(track['title'].strip().lower())) + extension.lower())
                  log('Track path = %s' % tFile)
                  mkdir_p(tPath)
                  shutil.copy(track['file'], tFile)
              #log(str(track))
    sys.exit()
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

