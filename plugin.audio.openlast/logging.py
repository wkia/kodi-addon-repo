# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

__addon__ = xbmcaddon.Addon(id='plugin.audio.openlast')
__addonid__ = __addon__.getAddonInfo('id')

def log(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"))

