#! /usr/bin/env python
# A class to parse ATOM-Feeds from Dicts/JSON

# taken from http://pastebucket.de/paste/749ce8de
# modified to accept specifying general info about the feed

import os
import sys
#import simplejson
import StringIO
#import Logger
import cgi

#try:
#	import feedparser
#except ImportError:
#	error = Logger.Error()
#	error.log("Can't locate Feedparser, download feedparser at %s" % ("http://www.feedparser.org/"))
#	error.log("-"*10)
#	error.log("Can't convert feed to dict/json")
#	error.dieonexit(0)
#	error.die(error.out())

example_dict = {
	'title': 'My feed',
	
	'item':{
		'a': {
			'description':'Hello&World',
			'content':'This is a sample Content',
			'comment': "This is a comment",
			'pubDate':'18 GMT 1202389 2010',
		},
		'b': {
			'description':'Second Item',
			'content':'I love dict2rss.py',
		},
	},

	'version':'0.1',
}


class dict2rss:
	def __init__(self, dict, language='en-en', description="auto-generated RSS with dict2rss"):
		self.title = ""
		self.version = "2.0"
		self.link = ""
		self.language = language
		self.description = description
		self.itemio = StringIO.StringIO()
		
		for key in dict:
			element = dict[key]
			if key == 'title': self.title = element
			elif key == 'version': self.version = element
			elif key == 'link': self.link = element
			elif key == 'language': self.language = element
			elif key == 'description': self.description = element
			elif 'dict' in str(type(element)) and key == 'item':
				"""Parse Items to XML-valid Data"""

				for child in dict[key]:
					print >>self.itemio, '		<item>'
					for childchild in dict[key][child]:
						if childchild == "comment":
							print >>self.itemio, "			<!-- %s -->" % (dict[key][child][childchild])
						else:
							try:
								if childchild in dict['cdata']:
									print >>self.itemio, '			<%s><![CDATA[%s]]></%s>'  % (childchild, cgi.escape(dict[key][child][childchild]), childchild)
								else: print >>self.itemio, '			<%s>%s</%s>'  % (childchild, cgi.escape(dict[key][child][childchild]), childchild)
							except: print >>self.itemio, '			<%s>%s</%s>'  % (childchild, cgi.escape(dict[key][child][childchild]), childchild)
					print >>self.itemio, '		</item>'
	def PrettyPrint(self):
		print self._out()
		
	def Print(self):
		print self._out().replace("	","")
		
	def TinyPrint(self):
		print self._out().replace("	","").replace("\n","")
        def toString(self):
                return self._out()
	def _out(self):
		d = """<?xml version="1.0" encoding="UTF-8"?>
		
<rss version="%s">
	<channel>
		<title>%s</title>
		<link>%s</link>
		<description>%s</description>
		<language>%s</language>""" % (self.version, self.title, self.link, self.description, self.language)
		d += self.itemio.getvalue()
		d += "	</channel>\n</rss>"
		return d

if __name__ == "__main__":		
	d = dict2rss(example_dict)
	d.TinyPrint()
