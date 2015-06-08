if command == '@ddg' or command == '@duckduckgo':
	def getResults(args,second=False):
		try:
			params = urllib.urlencode({
				'format':'json',
				'no_html':1,
				'q':args
			})
			res = json.loads(urllib.urlopen('http://api.duckduckgo.com/?'+params).read())
		except:
			return '\x02ERROR\x02: DuckDuckGo unreachable!'
		try:
			if res['AbstractText']!='' or (res['Definition']=='' and res['AbstractURL']!=''):
				title = HTMLParser.HTMLParser().unescape(urllib.unquote(res['AbstractText']))
				url = HTMLParser.HTMLParser().unescape(urllib.unquote(res['AbstractURL']))
				return title+' ('+url+')'
			elif res['Definition']!='':
				title = HTMLParser.HTMLParser().unescape(urllib.unquote(res['Definition']))
				url = HTMLParser.HTMLParser().unescape(urllib.unquote(res['DefinitionURL']))
				return title+' ('+url+')'
			elif len(res['Results'])>0:
				url = HTMLParser.HTMLParser().unescape(urllib.unquote(res['Results'][0]['FirstURL']))
				title = HTMLParser.HTMLParser().unescape(urllib.unquote(res['Results'][0]['Text']))
				return title+' - '+url
			elif res['Answer']!='':
				title = ' \\ '.join(HTMLParser.HTMLParser().unescape(urllib.unquote(res['Answer'])).split('\n'))
				return title
			elif res['Redirect']!='':
				return res['Redirect']
			elif second:
				return '\x02ERROR\x02: no solutions found.'
			else:
				return getResults('!ducky '+args,True)
		except:
			try:
				if res['Redirect']!='':
					return res['Redirect']
			except:
				pass
			if second:
				return '\x02ERROR\x02: no solutions found.'
			else:
				return getResults('!ducky '+args,True)
	s = getResults(args)
	print s
	send('[\x032DuckDuckGo\x0F] '+s)
	