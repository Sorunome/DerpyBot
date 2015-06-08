#!/usr/bin/python2 -Qnew
## -*- coding: utf-8 -*-

import threading,socket,string,time,sys,json,MySQLdb,traceback,errno,chardet,SocketServer,struct,signal,re,os,random,urllib,HTMLParser,chardet,math,random

#config handler
class Config:
	def __init__(self):
		self.readFile()
	def readFile(self):
		f = open('config.json')
		lines = f.readlines()
		self.json = json.loads("\n".join(lines))
		f.close()
	def save(self):
		f = open('config.json','w')
		json.dump(self.json,f)
		f.close()

#sql handler
class Sql():
	def __init__(self):
		global config
	def fetchOneAssoc(self,cur):
		data = cur.fetchone()
		if data == None:
			return None
		desc = cur.description
		dict = {}
		for (name,value) in zip(desc,data):
			dict[name[0]] = value
		return dict
	def query(self,q,p = []):
		global config
		try:
			db = MySQLdb.connect(config.json['sql']['server'],config.json['sql']['user'],config.json['sql']['passwd'],config.json['sql']['db'],charset='utf8')
			cur = db.cursor()
			for i in range(len(p)):
				try:
					try:
						p[i] = p[i].decode('utf-8').encode('utf-8')
					except:
						if p[i]!='':
							p[i] = p[i].decode(chardet.detect(p[i])['encoding']).encode('utf-8')
					p[i] = db.escape_string(p[i])
				except:
					if isinstance(p[i],basestring):
						try:
							p[i] = db.escape_string(p[i].encode('utf-8'))
						except:
							p[i] = db.escape_string(p[i])
			cur.execute(q % tuple(p))
			rows = []
			while True:
				row = self.fetchOneAssoc(cur)
				if row == None:
					break
				rows.append(row)
			cur.close()
			db.commit()
			db.close()
			return rows
		except Exception as inst:
			print('(sql) Error')
			print(inst)
			traceback.print_exc()
			return False

class RunPluginThread(threading.Thread):
	def __init__(self,file,variables):
		super(RunPluginThread,self).__init__()
		self.file = file
		self.variables = variables
	def run(self):
		execfile(self.file,self.variables,{})
class RunPlugin(threading.Thread):
	def __init__(self,file,variables):
		super(RunPlugin,self).__init__()
		self.file = file
		self.variables = variables
	def run(self):
		global plugins
		plugins.add(self)
		p = RunPluginThread(self.file,self.variables)
		
		p.start()
		plugins.add(p)
		startTime = time.time()
		while p.isAlive() and startTime + 10 > time.time():
			time.sleep(0.5)
		
		if p.isAlive():
			print self.file+': attempting to kill thread'
			p._Thread__stop()
			p.join()
			if not self.variables['hook']:
				self.variables['send']('\x02ERROR\x02: Plugin '+self.file+' received a timeout')
		plugins.remove(p)
		plugins.remove(self)

class PluginHandler():
	def __init__(self):
		self.chanToSendTo = ''
		self.plugins = []
	def add(self,p):
		self.plugins.append(p)
	def remove(self,p):
		self.plugins.remove(p)
	def verifyAdmin(self,ident,nick):
		global config
		for a in config.json['admins']:
			if a['nick']==nick and a['ident']==ident:
				return True
		return False
	def send(self,s,chan = '',mode = 'PRIVMSG'):
		global derp
		if chan == '':
			chan = self.chanToSendTo
		if '\n' in chan:
			return
		if not mode in ['PRIVMSG','NOTICE','TOPIC']:
			return
		s = ' \\ '.join(s.split('\n'))
		if len(s) > 400:
			s = s[0:400]+' ...'
		derp.send('%s %s :%s' % (mode,chan,s))
	def loadPlugin(self,plugin):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		if os.path.isfile(plugin):
			for p in config.json['plugins']:
				if p['file']==plugin:
					self.send('\x02ERROR\x02: plugin already loaded')
					return
			config.json['plugins'].append({
				'file':plugin,
				'channels':['*'],
				'hook':0,
				'lastHook':0
			});
			config.save()
			self.send('Plugin '+plugin+' loaded!')
		else:
			self.send('\x02ERROR\x02: plugin not found')
	def unloadPlugin(self,plugin):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		
		newPlugins = []
		found = False
		for p in config.json['plugins']:
			if p['file']!=plugin:
				newPlugins.append(p)
			else:
				found = True
		if found:
			config.json['plugins'] = newPlugins
			config.save()
			self.send('Removed plugin '+plugin)
		else:
			self.send('\x02ERROR\x02: plugin '+plugin+' not loaded')
	def setHook(self,plugin,hook):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		
		found = False
		for p in config.json['plugins']:
			if p['file']==plugin:
				found = True
				try:
					hook = int(hook)
				except:
					self.send('\x02ERROR\x02: hook isn\'t an integer')
					break
				p['hook'] = hook
				config.save()
				if hook != 0:
					self.send('Plugin '+plugin+' is now hooked at '+str(hook)+'s')
				else:
					self.send('Removed hook on Plugin '+plugin)
				break
		if not found:
			self.send('\x02ERROR\x02: plugin '+plugin+' not loaded')
	def addChan(self,plugin,chan):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		
		chan = chan.lower()
		found = False
		for p in config.json['plugins']:
			if p['file']==plugin:
				found = True
				if not (chan in p['channels']):
					p['channels'].append(chan)
					config.save()
					self.send('Enabled '+plugin+' in '+chan)
				else:
					self.send('\x02ERROR\x02: '+plugin+' already enabled in '+chan)
				break
		if not found:
			self.send('\x02ERROR\x02: plugin '+plugin+' not loaded')
	def remChan(self,plugin,chan):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		
		chan = chan.lower()
		found = False
		for p in config.json['plugins']:
			if p['file']==plugin:
				found = True
				if chan in p['channels']:
					p['channels'].remove(chan)
					config.save()
					self.send('Disabled '+plugin+' in '+chan)
				else:
					self.send('\x02ERROR\x02: '+plugin+' not enabled in '+chan)
				break
		if not found:
			self.send('\x02ERROR\x02: plugin '+plugin+' not loaded')
	def toggleList(self,plugin):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		
		found = False
		for p in config.json['plugins']:
			if p['file']==plugin:
				found = True
				if len(p['channels']) > 0 and p['channels'][0] == '*':
					p['channels'].remove('*')
					self.send('Plugin '+plugin+' is now in whitelist mode')
				else:
					p['channels'].insert(-0,'*')
					self.send('Plugin '+plugin+' is now in blacklist mode')
				config.save()
				break
		if not found:
			self.send('\x02ERROR\x02: plugin '+plugin+' not loaded')
	def listPlugins(self):
		global config
		s = ''
		for p in config.json['plugins']:
			s += p['file']+' '
		self.send('All plugins loaded: '+s[:-1])
	def listSinglePlugin(self,plugin):
		global config
		if not os.path.isfile(plugin):
			plugin += '.py'
		
		found = False
		for p in config.json['plugins']:
			if p['file'] == plugin:
				found = True
				s = plugin + ' '
				if len(p['channels']) > 0 and p['channels'][0] == '*':
					s += 'blacklist: '
				else:
					s+= 'whielist: '
				for c in p['channels']:
					if c!='*':
						s += c+' '
				s += ' Hook: '
				if p['hook']!=0:
					s += str(p['hook'])+'s'
				else:
					s += 'none'
				self.send(s)
				break
		if not found:
			self.send('\x02ERROR\x02: plugin '+plugin+' not loaded')
	def runHooks(self):
		global config
		variables = {
			'chan':'',
			'ident':'',
			'nick':'',
			'message':'',
			'admin':False,
			'json':json,
			'sql':sql,
			'command':'',
			're':re,
			'send':self.send,
			'time':time,
			'random':random,
			'socket':socket,
			'urllib':urllib,
			'args':'',
			'HTMLParser':HTMLParser,
			'math':math,
			'random':random,
			'hook':True
		}
		runTime = int(time.time())
		for plugin in config.json['plugins']:
			if plugin['hook'] > 0 and plugin['lastHook']+plugin['hook'] <= runTime:
				plugin['lastHook'] = runTime
				RunPlugin(plugin['file'],variables).start()
		config.save()
	def handleMessage(self,chan,ident,nick,message):
		global sql,config,derp
		chan = chan.lower()
		self.chanToSendTo = chan
		if chan[0]!='#':
			self.chanToSendTo = nick
		admin = self.verifyAdmin(ident,nick)
		command = message.split(' ')[0].lower()
		if command != message:
			args = ' '.join(message.split(' ')[1:])
		else:
			args = ''
		
		if admin and command == '>load':
			self.loadPlugin(args)
		elif admin and command == '>unload':
			self.unloadPlugin(args)
		elif admin and (command == '>sethook' or command == '>addhook' or command == '>hook'):
			if len(args.split(' '))==1:
				self.send('\x02ERROR\x02: invalid use. >sethook [plugin] [seconds]')
			else:
				self.setHook(args.split(' ')[0],args.split(' ')[1])
		elif admin and command == '>remhook':
			self.setHook(args,'0')
		elif admin and (command == '>activate' or command == '>enable' or command == '>addlist'):
			if len(args.split(' '))==1:
				self.send('\x02ERROR\x02: invalid use. >addlist [plugin] [channel]')
			else:
				self.addChan(args.split(' ')[0],args.split(' ')[1])
		elif admin and (command == '>deactivate' or command == '>disable' or command == '>remlist'):
			if len(args.split(' '))==1:
				self.send('\x02ERROR\x02: invalid use. >remlist [plugin] [channel]')
			else:
				self.remChan(args.split(' ')[0],args.split(' ')[1])
		elif admin and command == '>togglelist':
			self.toggleList(args)
		elif admin and command == '>list':
			if args == '':
				self.listPlugins()
			else:
				self.listSinglePlugin(args)
		elif admin and command == '>join':
			if args[0] == '#':
				for chan in config.json['channels']:
					if chan==args:
						self.send('\x02ERROR\x02: already in channel')
						break
				else:
					derp.send('JOIN %s' % args)
					config.json['channels'].append(args)
					config.save()
			else:
				self.send('\x02ERROR\x02: not a valid channel')
		elif admin and command == '>part' and chan[0]=='#':
			derp.send('PART %s' % chan)
			config.json['channels'].remove(chan)
			config.save()
		elif admin and command == '>raw':
			derp.send(args)
		
		variables = {
			'chan':chan,
			'ident':ident,
			'nick':nick,
			'message':message,
			'admin':admin,
			'json':json,
			'sql':sql,
			'command':command,
			're':re,
			'send':self.send,
			'time':time,
			'random':random,
			'socket':socket,
			'urllib':urllib,
			'args':args,
			'HTMLParser':HTMLParser,
			'math':math,
			'random':random,
			'hook':False
		}
		for plugin in config.json['plugins']:
			if len(plugin['channels']) > 0 and ((plugin['channels'][0] == '*' and not (chan in plugin['channels'])) or (plugin['channels'][0] != '*' and (chan in plugin['channels']))):
				RunPlugin(plugin['file'],variables).start()
		
		return
	def killPlugins(self):
		for p in self.plugins:
			try:
				p._Thread__stop()
			except:
				traceback.print_exc()
		self.plugins = []
#irc bot
class Bot(threading.Thread):
	def __init__(self,server,port,nick,ns,ch):
		threading.Thread.__init__(self)
		self.stopnow = False
		self.restart = False
		self.server = server
		self.port = port
		self.nick = nick
		self.ns = ns
		self.userlist = {}
		self.chans = {}
		self.chans = ch
		
		self.oircNormalLinePattern = re.compile('^(?:\x03?[0-9]{0,2}\([#OCS]\)\x0F?)<([^>]+)> (.*)')
	def stopThread(self):
		print('Giving signal to quit irc bot...')
		#self.s.close()
		self.stopnow = True
		self.restart = False
	def send(self,s):
		try:
			try:
				s = s.decode('utf-8').encode('utf-8')
			except:
				try:
					s = s.encode('utf-8')
				except:
					if s!='':
						s = s.decode(chardet.detect(s)['encoding']).encode('ascii')
			self.s.sendall('%s\r\n' % str(s))
			print('<< '+s)
		except:
			traceback.print_exc()
			self.restart = True
			self.stopnow = True
	def connectToIRC(self):
		self.s = socket.socket()
		self.s.settimeout(0.5)
		self.s.connect((self.server,self.port))
		self.send('USER %s %s %s :%s' % ('DerpyBot','host','server',self.nick))
		self.send('NICK %s' % (self.nick))
	def addUser(self,u,c):
		if self.userlist.has_key(c):
			self.userlist[c].append(u)
		else:
			self.userlist[c] = [u]
	def removeUser(self,u,c):
		global sql
		if self.userlist.has_key(c):
			self.userlist[c].remove(u)
	def handleQuit(self,n,m):
		global handle
		for c,us in self.userlist.iteritems():
			for u in us:
				if u==n:
					self.removeUser(n,c)
	def handleNickChange(self,old,new):
		global handle
		for c,us in self.userlist.iteritems():
			for u in us:
				if u==old:
					self.removeUser(old,c)
					self.addUser(new,c)
		return False
	def doMain(self,line):
		global handle,config,plugins
		message = ' '.join(line[3:])[1:]
		nick = line[0].split('!')[0][1:]
		chan = line[2]
		if chan[0]==':':
			chan = chan[1:]
		if line[1]=='PRIVMSG': # TODO: Parse OmnomIRC
			
			if line[3]==':\x01ACTION' and message[-1:]=='\x01':
				print('action')
			else:
				ident = line[0].split('!')[1]
				if nick == '^': # omnomirc
					m = self.oircNormalLinePattern.match(message)
					if m:
						nick = m.group(1)
						message = m.group(2)
						ident = nick+'@omnomirc'
					else:
						return
				plugins.handleMessage(chan,ident,nick,message)
		elif line[1]=='JOIN':
			self.addUser(nick,chan)
			if nick.lower()==self.nick.lower():
				self.getUsersInChan(chan)
		elif line[1]=='PART':
			self.removeUser(nick,chan)
			if nick.lower()==self.nick.lower():
				self.delUsersInChan(chan)
		elif line[1]=='QUIT':
			self.handleQuit(nick,' '.join(line[2:])[1:])
		elif line[1]=='MODE':
			print('mode change')
		elif line[1]=='KICK':
			self.removeUser(line[3],chan)
		elif line[1]=='TOPIC':
			print('topic change')
		elif line[1]=='NICK':
			self.handleNickChange(nick,line[2][1:])
		elif line[1]=='352':
			self.addUser(line[7],line[3])
	def serve(self):
		global sql
		print('Entering main loop')
		lastPingTime = time.time()
		lastLineTime = time.time()
		quitMsg = 'Bye!';
		while not self.stopnow:
			try:
				self.readbuffer += self.s.recv(1024)
			except socket.error as e:
				if isinstance(e.args,tuple):
					if e == errno.EPIPE:
						self.stopnow = True
						self.restart = True
						quitMsg = 'Being stupid'
						print('Restarting due to stupidness ('+str(self.i)+add)
					elif e == errno.ECONNRESET:
						self.stopnow = True
						self.restart = True
						quitMsg = 'Being very stupid'
						print('Restarting because connection being reset by peer')
				time.sleep(0.1)
				if lastLineTime+90 <= time.time(): # allow up to 60 seconds lag
					self.stopnow = True
					self.restart = True
					lastLineTime = time.time()
					quitMsg = 'No pings (1)'
					print('Restarting due to no pings ('+str(self.i)+add)
			except Exception as inst:
				print(inst)
				traceback.print_exc()
				time.sleep(0.1)
				if lastLineTime+90 <= time.time(): # allow up to 60 seconds lag
					self.stopnow = True
					self.restart = True
					lastLineTime = time.time()
					quitMsg = 'No pings (2)'
					print('Restarting due to no pings ('+str(self.i)+add)
			temp=string.split(self.readbuffer,'\n')
			self.readbuffer=temp.pop()
			if lastPingTime+90 <= time.time(): # allow up to 60 seconds lag
				self.stopnow = True
				self.restart = True
				lastLineTime = time.time()
				quitMsg = 'No pings(3)'
				return
			if lastPingTime+30 <= time.time():
				self.send('PING %s' % time.time())
				lastPingTime = time.time()
			
			try:
				plugins.runHooks()
			except Exception as inst:
				print(inst)
				traceback.print_exc()
			
			for line in temp:
				print('>> '+line)
				line=string.rstrip(line)
				line=string.split(line)
				try:
					lastLineTime = time.time()
					if(line[0]=='PING'):
						self.send('PONG %s' % line[1],True)
						continue
					if line[0]=='ERROR' and 'Closing Link' in line[1]:
						time.sleep(30)
						self.stopnow = True
						self.restart = True
						quitMsg = 'Closed link'
						print('Error when connecting, restarting bot ('+str(self.i)+add)
						return
					self.doMain(line)
				except Exception as inst:
					print('parse Error')
					print(inst)
					traceback.print_exc()
		self.send('QUIT :%s' % quitMsg)
		self.handleQuit(self.nick,quitMsg)
		try:
			self.s.close()
		except:
			pass
		if self.restart:
			print('Restarting bot')
			time.sleep(15)
			self.run()
	def delUsersInChan(self,c):
		if self.userlist.has_key(c):
			self.userlist[c] = []
	def getUsersInChan(self,c):
		self.delUsersInChan(c)
		self.send('WHO %s' % c)
	def joinChans(self):
		for c in self.chans:
			self.send('JOIN %s' % c)
	def run(self):
		global sql
		self.restart = False
		self.stopnow = False
		print('Starting bot...')
		
		self.connectToIRC()
		self.readbuffer = ''
		motdEnd = False
		identified = False
		identifiedStep = 0
		if self.ns=='':
			identified = True
		while not self.stopnow and not (motdEnd and identified):
			try:
				self.readbuffer += self.s.recv(1024)
			except Exception as inst:
				print(inst)
				traceback.print_exc()
			temp=string.split(self.readbuffer,'\n')
			self.readbuffer=temp.pop()
			for line in temp:
				print('>> '+line)
				line=string.rstrip(line)
				line=string.split(line)
				try:
					if line[0]=='PING':
						self.send('PONG %s' % line[1])
						continue
					if line[1]=='376':
						motdEnd = True
					if not identified and ((line[1] == 'NOTICE' and 'NickServ' in line[0])):
						if identifiedStep==0:
							self.send('PRIVMSG NickServ :IDENTIFY %s' % self.ns)
							identifiedStep = 1
						elif identifiedStep==1:
							identified = True
				except Exception as inst:
					print(inst)
					traceback.print_exc()
		self.joinChans()
		self.serve()


config = Config()
sql = Sql()
plugins = PluginHandler()
derp = Bot(config.json['irc']['server'],config.json['irc']['port'],config.json['irc']['nick'],config.json['irc']['nickserv'],config.json['channels'])
derp.start()
try:
	while True:
		time.sleep(60)
except KeyboardInterrupt:
	derp.stopThread()
	plugins.killPlugins()
