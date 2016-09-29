# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

def log(txt, session):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u'%s - %s: %s' % (__addonid__, session, txt)
    xbmc.log(msg=message.encode("utf-8"))

