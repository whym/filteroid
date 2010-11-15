#! /usr/bin/env python
# -*- coding: utf-8 -*-

# abuselog to RSS

# sample:
# http://localhost:8080/beta/mwabuselog?mwhome=http%3A//ja.wikipedia.org

from xml.dom import minidom
import urlparse
import urllib
import sys
import re
import cgi
import yaml
import os
import datetime

sys.path.append(os.path.dirname(__file__))

# fix user agent for wikimedia.org's preference
from urllib import FancyURLopener
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'
myopener = MyOpener()
urllib.urlopen = myopener.open
urllib.urlretrieve = myopener.retrieve

def shorten_url(url, shortener, tag='shortUrl'):
    doc = minidom.parseString(urllib.urlopen(shortener % urllib.quote(url)).read())
    elems = doc.getElementsByTagName(tag)
    if len(elems) > 0:
        url = elems[0].firstChild.data
    return url

def open_file(filename):
    if os.path.isfile(filename):
        return open(filename)
    else:
        filename = os.path.sep.join([os.path.dirname(__file__), os.path.basename(filename)])
        if os.path.isfile(filename):
            return open(filename)
    return None

def get_args():
    f = open_file('mwabuselog.yaml')
    if f:
        ret = yaml.load(f)
    if not ret:
        ret = {}
    args = cgi.FieldStorage(keep_blank_values=True)
    for k in args.keys():
        ret[k] = args.getlist(k).pop()
    return ret

def is_valid_uri(s):
    return s.index(':') > 0

def get_sitename(mwhome):
    url = '%s/w/api.php?format=xml&action=query&meta=siteinfo' % mwhome
    doc = minidom.parseString(urllib.urlopen(url).read())
    elems = doc.getElementsByTagName('general')
    if len(elems) > 0:
        return '%s (%s)' % (elems[0].attributes['sitename'].value, elems[0].attributes['wikiid'].value)
    return None

if __name__ == '__main__':
    # TODO: エラーの時は text/plain などにする
    # TODO: アイテム抽出の結果、URL短縮の結果を datastore にキャッシュする

    mwhome = 'http://en.wikipedia.org'
    query = ''
    format = '%s: [[%s]] __PAGE__ %s'
    limit = '15'
    targets = 'result|title|filter|timestamp|ids'
    filter_results = re.compile('^(warn|)$')
    shortener = None

    args = get_args()
    if args.has_key('mwhome'):
        mwhome = args['mwhome']
    if args.has_key('limit'):
        limit = args['limit']
    if args.has_key('format'):
        format = args['format']
    if args.has_key('targets'):
        targets = args['targets']
    if args.has_key('shortener'):
        shortener = args['shortener']
        if not is_valid_uri(shortener):
            shortener = None
    if args.has_key('filter'):
        filter_results = re.compile(args['filter'])

    if not mwhome:
        print 'Content-Type: text/html'
        print ''
        print '<title>no nwhome provided</title>'
        print '<h1>no mwhome provided</h1>'
        # import pprint
        # import os
        # print '<pre>'
        # pp = pprint.PrettyPrinter(width=80)
        # pp.pprint(dict(os.environ))
        # pp.pprint(dict(args))
        # print '</pre>'
        sys.exit()

    sitename = get_sitename(mwhome)
    # TODO: remove illegal arguments
    uri = "%s/w/api.php?format=xml&action=query&list=abuselog&afllimit=%s&aflprop=%s" % (mwhome, limit, targets)
    itemtag = 'item'
    uri = urllib.urlopen(uri)
    host = urlparse.urlparse(uri.geturl()).hostname
    xmlstr = uri.read()
    doc = minidom.parseString(xmlstr)
    items = {}#Sat, 13 Nov 2010 09:59:30 GMT

    # 'ids' corresponds to 'id' and 'filter_id'
    targets = targets.replace('ids', 'id|filter_id')

    formatsize = len(format.split('%s')) - 1
    
    for item in doc.getElementsByTagName(itemtag):
        formatted = format % tuple([item.attributes[x].value for x in targets.split('|')][0:formatsize])

        # pass only the items with pre-defined results
        result = item.attributes['result'].value or ''
        if filter_results.match(result):
            None
        else:
            continue

        if item.attributes.has_key('title'):
            pagelink = '%s/wiki/%s' % (mwhome, urllib.quote(item.attributes['title'].value.encode('utf-8')))
            if shortener:
                pagelink = shorten_url(pagelink.encode('utf-8'), shortener)
            formatted = formatted.replace('__PAGE__', pagelink)
        logid = item.attributes['id'].value
        pubdate = datetime.datetime.strptime(item.attributes['timestamp'].value, "%Y-%m-%dT%H:%M:%SZ")
        pubdate = pubdate.strftime("%a, %d %b %Y %H:%M:%S GMT")
        link = '%s/wiki/Special:AbuseLog/%s' % (mwhome, logid)
        if shortener:
            link = shorten_url(link.encode('utf-8'), shortener)
        items[logid] = {
            'description': formatted,
            'link': link,
            'pubDate': pubdate,
            # TODO: parse the mod date and add as an attribute here
        }

    def printheader(header,original,default=None):
        x = original.info().getheader(header)
        if x or default:
            print '%s: %s' % (header, x if x else default)
    
    import dict2rss
    content = dict2rss.dict2rss({'title': sitename + ' AbuseLog',
                                 'description': 'auto-generated from the data available at ' + mwhome + '/wiki/Special:AbuseLog',
                                 'link': 'http://filteroid.appspot.com',
                                 'item': items})._out().encode('utf-8')
    printheader('Last-Modified', uri)
    printheader('Content-Type', uri, 'text/xml; charset="UTF-8"')
    print ''
    print content
