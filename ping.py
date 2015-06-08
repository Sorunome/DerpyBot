if command == '@ping':
	success = True
	try:
		a = urllib.urlopen(args)
	except:
		try:
			a = urllib.urlopen('http://'+args)
		except:
			send('[\x032ping\x0F] unkown host '+args)
			success = False
	if success:
		if a.getcode() == 200:
			send('[\x032ping\x0F] Successfully pinged '+args+' (200)')
		else:
			send('[\x032ping\x0F] Error pinging '+args+' ('+str(a.getcode())+')')