#! /usr/bin/env python
# -*- coding: utf-8 -*-

# link extractor for rss

# sample:
# http://localhost:8080/beta/rsslinker?uri=http%3A//ja.wikipedia.org/w/index.php%3Ftitle%3DTemplate%3A%25E6%2596%25B0%25E3%2581%2597%25E3%2581%2584%25E8%25A8%2598%25E4%25BA%258B%26feed%3Drss%26action%3Dhistory&target=description&span=<p>.*</p>

from xml.dom import minidom
import urlparse
import urllib
import sys
import re
import cgi
import yaml
import os

# fix user agent for wikimedia.org's preference
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
    args = cgi.FieldStorage(keep_blank_values=True)
    for k in args.keys():
        ret[k] = args.getlist(k).pop()
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
    # TODO: エラーの時は text/plain などにする
    # TODO: アイテム抽出の結果、URL短縮の結果を datastore にキャッシュする

    uri = None
    targettag = 'description'
    span_pat = r'.+'
    shortener = None
    itemtag = 'item'
    delimiter = ' '
    format = '%s %s'

    args = get_args()
    if args.has_key('uri'):
        uri = args['uri']
    if args.has_key('target'):
        targettag = args['target']
    if args.has_key('span'):
        span_pat = re.compile(args['span'])
    if args.has_key('shortener'):
        shortener = args['shortener']
    if args.has_key('delimiter'):
        delimiter = args['delimiter']
    if args.has_key('format'):
        format = args['format']

    if not uri:
        print 'Content-Type: text/html'
        print ''
        print '<title>no uri provided</title>'
        print '<h1>no uri provided</h1>'
        # import pprint
        # import os
        # print '<pre>'
        # pp = pprint.PrettyPrinter(width=80)
        # pp.pprint(dict(os.environ))
        # pp.pprint(dict(args))
        # print '</pre>'
        sys.exit()

    uri = urllib.urlopen(uri)
    host = urlparse.urlparse(uri.geturl()).hostname
    original_rss = uri.read()
    doc = minidom.parseString(original_rss)
    for item in doc.getElementsByTagName(itemtag):
        for x in item.getElementsByTagName(targettag):
            for text in filter(lambda x: x.nodeType == 3, x.childNodes):
                links = []
                html = text.data
                for m in re.finditer(span_pat, html):
                    start,end = m.span()
                    links += extract_links(html[start:end])

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
                    res = delimiter.join([format % (x,y) for (x,y) in res])
                    text.data = res

    def printheader(header,original,default=None):
        x = original.info().getheader(header)
        if x or default:
            print '%s: %s' % (header, x if x else default)
    
    printheader('Last-Modified', uri)
    printheader('Content-Type', uri, 'text/xml; charset="UTF-8"')
    print ''
    print doc.toxml().encode('utf-8')
