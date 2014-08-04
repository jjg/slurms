#!/usr/bin/python

import httplib, urllib, json, getpass
from subprocess import call
import Adafruit_CharLCD as LCD
import smtplib

# config
email = 'flactester@murfie.com'
password = 'T35T1NGMurf13'

# globals
authtoken = ''
nowPlayingDisc = 0
totalDisccount = 0
noticeCount = 0
warnCount = 0
errorCount = 0

# API http bits
conn = httplib.HTTPSConnection('api.murfie.com')

# init lcd library for pi plate
lcd = LCD.Adafruit_CharLCDPlate()

def logMessage(message, level):

	print(message)

	if level == 'notice':
		global noticeCount
		noticeCount = noticeCount + 1 
		lcd.set_color(1.0, 1.0, 1.0)

	if level == 'warn':
		global warnCount
		warnCount = warnCount + 1
		lcd.set_color(0.0, 1.0, 1.0)

	if level == 'error':
		global errorCount
		errorCount = errorCount + 1
		lcd.set_color(1.0, 0.0, 0.0)

	lcd.clear()
	lcd.message(message)
	lcd.message('\nn:%s w:%s e:%s' % (noticeCount, warnCount, errorCount))

	# notify jason of errors
	if level == 'error':

		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.startttls()
		server.login('jason@murfie.com','backinblack')

		server.sendmail('jason@murfie.com', '9203199152@vtext.com', message)

def authenticate(email, password):

	logMessage('authenticating', 'notice')

	try:
		# get the token
		params = urllib.urlencode({'email':email, 'password':password})
		headers = {'Content-type':'application/x-www-form-urlencoded','Accept':'text/plain'}
		conn.request('POST', '/api/tokens', params, headers)
		response = conn.getresponse()

		apiResult = json.loads(response.read())
		conn.close()

		return apiResult['user']['token']

	except(ex):
		logMessage('error authenticating, ' + ex, 'error')
		return None

def pickDisc():

	# get the album list
	try:
		conn.request('GET', '/api/discs.json?auth_token=' + authtoken + '&device=slurms')
		response = conn.getresponse()
		apijson = json.loads(response.read())

 	except(ex):
		logMessage('error loading albums: ' + ex, 'error')
 		return None

	# select the disc to play
	try:
		global totalDiscCount
		totalDiscCount = len(apijson)

		selecteddisc = nowPlayingDisc
		selecteddiscid = apijson[selecteddisc]['disc']['id']
		print("\n%s by %s selected" % (apijson[selecteddisc]['disc']['album']['title'],apijson[selecteddisc]['disc']['album']['main_artist']))

	except(ex):
		logMessage('error selecting disc: ' + ex, 'error')
		return None
	
	# get tracks for selected disc
	try:
		conn.request('GET', '/api/discs/%d.json?auth_token=%s' % (apijson[selecteddisc]['disc']['id'], authtoken + '&device=slurms'))
		response = conn.getresponse()
		apiResult = json.loads(response.read())

		conn.close()
		disc = apiResult['disc']

		return disc

	except(ex):
		logMessage('error loading tracks: ' + ex, 'error')
		return None 

def playDisc(disc):

	# play each track in the disc
	for track in disc['tracks']:

		try:
			logMessage(track['title'], 'notice')

			#logMessage('%s \n by %s' % (track['title'], disc['album']['main_artist']), 'notice')

			# get the media Uri
			conn.request('GET', '/api/discs/%s/tracks/%s.json?auth_token=%s' % (disc['id'],track['id'],authtoken + '&device=slurms'))
			response = conn.getresponse()
			apiResult = json.loads(response.read())
			conn.close()
			mediaUri = '\"%s\"' % apiResult['track']['url']

			mediaUri = mediaUri.replace('https', 'http')

			call('mplayer -quiet %s' % mediaUri, shell=True)

		except(ex):
			logMessage('error playing track: ' + ex, 'error')

	# when the disc is over, select another
	global nowPlayingDisc
	nowPlayingDisc = nowPlayingDisc + 1

	if nowPlayingDisc < totalDiscCount:
		logMessage('so tired of partying...', 'warn')
		playDisc(pickDisc())
	else:
		logMessage('Can I stop parytying now?', 'warn')

# start by authenticating
logMessage('Wibby wam wam wozzel!', 'notice')

authtoken = authenticate(email, password)
playDisc(pickDisc())
