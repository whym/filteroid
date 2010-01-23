#! /usr/bin/env python
# -*- encoding: utf-8 -*-

# link extractor for rss

# sample:
# http://localhost:8080/beta/rss?uri=http://whym.tumblr.com/rss&fil=&sub=

from xml.dom import minidom
import urlparse
import urllib
import sys
import re
from cgi import parse_qsl
import yaml
import os

from urllib import FancyURLopener
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'
myopener = MyOpener()
urllib.urlopen = myopener.open
urllib.urlretrieve = myopener.retrieve

def get_args():
    ret = yaml.load(open('rsslinker.yaml'))
    if not ret:
        ret = {}
    args = os.environ
    if args.has_key('QUERY_STRING'):
        for (x,y) in parse_qsl(args['QUERY_STRING']):
            ret[x] = y
    return ret

def extract_links(html):
    ret = []
    for m in re.finditer(r'<a .*?href="(.*?)".*?>(.*?)</a>', html):
        ret.append((m.group(2), m.group(1)))
    return ret

def shorten_url(url, shortener, tag='shortUrl'):
    doc = minidom.parseString(urllib.urlopen(shortener % urllib.quote(url)).read())
    url = doc.getElementsByTagName(tag)[0].firstChild.data
    return url

if __name__ == '__main__':
    print 'Content-Type: text/xml; charset="UTF-8"'
    print ''

    uri = None
    targettag = 'description'
    span_pat = r'.*'
    shortener = None
    itemtag = 'item'

    h = get_args()
    if h.has_key('uri'):
        uri = h['uri']
    if h.has_key('target'):
        targettag = h['target']
    if h.has_key('span'):
        span_pat = re.compile(h['span'])
    if h.has_key('shortener'):
        shortener = h['shortener']

    if not uri:
        print '<error>no uri provided</error>'
        sys.exit()

    host = urlparse.urlparse(uri).hostname

    original_rss = urllib.urlopen(uri).read()
    doc = minidom.parseString(original_rss)
    for item in doc.getElementsByTagName(itemtag):
        for x in item.getElementsByTagName(targettag):
            for text in filter(lambda x: x.nodeType == 3, x.childNodes):
                html = text.data
                for m in re.finditer(span_pat, html):
                    start,end = m.span()
                    html = html[start:end]
                links = extract_links(html)

                res = []
                for (title,path) in links:
                    if path.startswith('/'):
                        path = 'http://' + host + path
                    if shortener:
                        path = shorten_url(path, shortener)
                    res.append((title, path))
                if len(res) == 0:
                    item.parentNode.removeChild(item)
                else:
                    res = ', '.join([x+' '+y for (x,y) in res])
                    text.data = res

    # TODO: description 空のとき、 item ごと削除する
    print doc.toxml().encode('utf-8')
