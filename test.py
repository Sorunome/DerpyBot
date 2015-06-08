if message.lower() == 'test':
	if random.randint(0,3) == 0:
		send('Test received')
	else:
		send('Test failed')

if message.lower() == 'ping' or message.lower() == 'pong' or message.lower() == 'pang' or message.lower() == 'pung':
	s = message
	print message[1]
	if message[1].lower()=='i' or message[1].lower()=='a':
		s = s.replace('i','o')
		s = s.replace('I','O')
		s = s.replace('a','u')
		s = s.replace('A','U')
	else:
		s = s.replace('o','i')
		s = s.replace('O','I')
		s = s.replace('u','a')
		s = s.replace('U','A')
	send(s)
if message.lower() == 'peng':
	if random.randint(0,14) == 0:
		send('*click*')
	else:
		send('BOOOOOM')
if message.lower() == 'pyng':
	send('Ok, that is looking really ugly')
if message.lower() == 'marco':
	send('Polo')
if message.lower() == 'boop':
	send(message+' '+message)
