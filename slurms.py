#!/usr/bin/python

import httplib, urllib, json, getpass
from subprocess import call
import Adafruit_CharLCD as LCD

# config
email = 'flactester@murfie.com'
password = 'T35T1NGMurf13'

# globals
authtoken = ''
nowPlayingDisc = 0
totalDisccount = 0

# API http bits
conn = httplib.HTTPSConnection('api.murfie.com')

# init lcd library for pi plate
lcd = LCD.Adafruit_CharLCDPlate()

def logMessage(message, level):

	print(message)

	if level == 'notice':
		lcd.set_color(1.0, 1.0, 1.0)

	if level == 'warn':
		lcd.set_color(0.0, 1.0, 1.0)

	if level == 'error':
		lcd.set_color(1.0, 0.0, 0.0)

	lcd.clear()
	lcd.message(message)

def authenticate(email, password):

	logMessage('authenticating', 'notice')

	# gather the authentication credentials
	#email = raw_input('Email:')
	#password = getpass.getpass()

	# get the token
	params = urllib.urlencode({'email':email, 'password':password})
	headers = {'Content-type':'application/x-www-form-urlencoded','Accept':'text/plain'}
	conn.request('POST', '/api/tokens', params, headers)
	response = conn.getresponse()

	apiResult = json.loads(response.read())
	conn.close()

	return apiResult['user']['token']

def pickDisc():

	logMessage('picking next disc', 'notice')

	# get the album list
	conn.request('GET', '/api/discs.json?auth_token=' + authtoken)
	response = conn.getresponse()
	apijson = json.loads(response.read())
	#discindex = 0
	#for disc in apijson:
	#	print discindex, disc['disc']['album']['title']
	#	discindex += 1

	global totalDiscCount
	totalDiscCount = len(apijson)

	selecteddisc = nowPlayingDisc  #int(raw_input('\nDisc to play: '))
	selecteddiscid = apijson[selecteddisc]['disc']['id']
	print("\n%s by %s selected" % (apijson[selecteddisc]['disc']['album']['title'],apijson[selecteddisc]['disc']['album']['main_artist']))

	# get tracks for selected disc
	conn.request('GET', '/api/discs/%d.json?auth_token=%s' % (apijson[selecteddisc]['disc']['id'], authtoken))
	response = conn.getresponse()
	apiResult = json.loads(response.read())

	conn.close()
	disc = apiResult['disc']

	return disc

def playDisc(disc):

	# play each track in the disc
	for track in disc['tracks']:

		try:
			logMessage('%s \n by %s' % (track['title'], disc['album']['main_artist']), 'notice')

			# get the media Uri
			conn.request('GET', '/api/discs/%s/tracks/%s.json?auth_token=%s' % (disc['id'],track['id'],authtoken))
			response = conn.getresponse()
			apiResult = json.loads(response.read())
			conn.close()
			mediaUri = '\"%s\"' % apiResult['track']['url']

			mediaUri = mediaUri.replace('https', 'http')

			call('mplayer -quiet %s' % mediaUri, shell=True)

		except(ex):
			logMessage(ex, 'error')

	# when the disc is over, select another
	global nowPlayingDisc
	nowPlayingDisc = nowPlayingDisc + 1

	if nowPlayingDisc < totalDiscCount:
		logMessage('so tired of partying...', 'warn')
		playDisc(pickDisc())

# start by authenticating
logMessage('Wibby wam wam wozzel!', 'notice')

authtoken = authenticate(email, password)
playDisc(pickDisc())
