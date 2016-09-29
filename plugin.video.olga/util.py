# -*- coding: utf-8 -*-

import urllib

def build_url(baseUrl, query):
    return baseUrl + '?' + urllib.urlencode(query)

