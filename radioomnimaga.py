if hook:
	f = open('radioomnimaga.json')
	lastTitle = json.loads('\n'.join(f.readlines()))['lastRadioTitle']
	f.close()
	
	f = open('cursong.json')
	newSong = json.loads('\n'.join(f.readlines()))
	if newSong['title'] != lastTitle:
		f = open('radioomnimaga.json','w')
		json.dump({
			'lastRadioTitle':newSong['title']
		},f)
		f.close()
		
		message = '\x0310Now playing \x033'+newSong['artist']+'\x0310 - \x034'+newSong['title']+' \x0F(\x0312http://radio.ourl.ca\x0F)'
		topic = 'http://omnimaga.org | Omnimaga Radio'
		send(topic+' | '+message,'#radio','TOPIC')