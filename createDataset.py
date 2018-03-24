import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

personName = raw_input('Enter your full name: ')
fbData = raw_input('Do you have Facebook data to parse through (y/n)?')
googleData = raw_input('Do you have Google Hangouts data to parse through (y/n)?')
linkedInData = raw_input('Do you have LinkedIn data to parse through (y/n)?')
iosData = raw_input('Do you have ios data to parse through (y/n)?')

def getGoogleHangoutsData():
	# Putting all the file names in a list
	allFiles = []
	# Edit these file and directory names if you have them saved somewhere else
	for filename in os.listdir('GoogleTextForm'):
	    if filename.endswith(".txt"):
	        allFiles.append('GoogleTextForm/' + filename)

	responseDictionary = dict() # The key is the other person's message, and the value is my response
	# Going through each file, and recording everyone's messages to me, and my responses
	for currentFile in allFiles:
		myMessage, otherPersonsMessage, currentSpeaker = "","",""
		openedFile = open(currentFile, 'r')
		allLines = openedFile.readlines()
	   	for index,lines in enumerate(allLines):
	   		# The sender's name is separated by < and >
	   	    leftBracket = lines.find('<')
	   	    rightBracket = lines.find('>')

	        # Find messages that I sent
	   	    if (lines[leftBracket+1:rightBracket] == personName):
	   	        if not myMessage:
	   	            # Want to find the first message that I send (if I send multiple in a row)
	   	            startMessageIndex = index - 1
	   	        myMessage += lines[rightBracket+1:]

	   	    elif myMessage:
	   	        # Now go and see what message the other person sent by looking at previous messages
	   	        for counter in range(startMessageIndex, 0, -1):
	   	            currentLine = allLines[counter]
	                # In case the message above isn't in the right format
	   	            if (currentLine.find('<') < 0 or currentLine.find('>') < 0):
	   	                myMessage, otherPersonsMessage, currentSpeaker = "","",""
	   	                break
	   	            if not currentSpeaker:
	   	                # The first speaker not named me
	   	                currentSpeaker = currentLine[currentLine.find('<')+1:currentLine.find('>')]
	   	            elif (currentSpeaker != currentLine[currentLine.find('<')+1:currentLine.find('>')]):
	   	                # A different person started speaking, so now I know that the first person's message is done
		                otherPersonsMessage = cleanMessage(otherPersonsMessage)
		                myMessage = cleanMessage(myMessage)
	   	                responseDictionary[otherPersonsMessage] = myMessage
	   	                break
	   	            otherPersonsMessage = currentLine[currentLine.find('>')+1:] + otherPersonsMessage
	   	        myMessage, otherPersonsMessage, currentSpeaker = "","",""
	return responseDictionary

def getFacebookData():
	responseDictionary = dict()
	fbFile = open('fbMessages.txt', 'r')
	allLines = fbFile.readlines()
	myMessage, otherPersonsMessage, currentSpeaker = "","",""
	for index,lines in enumerate(allLines):
	    rightBracket = lines.find(']') + 2
	    justMessage = lines[rightBracket:]
	    colon = justMessage.find(':')
	    # Find messages that I sent
	    if (justMessage[:colon] == personName):
	        if not myMessage:
	            # Want to find the first message that I send (if I send multiple in a row)
	            startMessageIndex = index - 1
	        myMessage += justMessage[colon+2:]

	    elif myMessage:
	        # Now go and see what message the other person sent by looking at previous messages
	        for counter in range(startMessageIndex, 0, -1):
	            currentLine = allLines[counter]
	            rightBracket = currentLine.find(']') + 2
	            justMessage = currentLine[rightBracket:]
	            colon = justMessage.find(':')
	            if not currentSpeaker:
	                # The first speaker not named me
	                currentSpeaker = justMessage[:colon]
	            elif (currentSpeaker != justMessage[:colon] and otherPersonsMessage):
	                # A different person started speaking, so now I know that the first person's message is done
	                otherPersonsMessage = cleanMessage(otherPersonsMessage)
	                myMessage = cleanMessage(myMessage)
	                responseDictionary[otherPersonsMessage] = myMessage
	                break
	            otherPersonsMessage = justMessage[colon+2:] + otherPersonsMessage
	        myMessage, otherPersonsMessage, currentSpeaker = "","",""
	return responseDictionary

def getLinkedInData():
	df = pd.read_csv('Inbox.csv')
	dateTimeConverter = lambda x: datetime.strptime(x,'%B %d, %Y, %I:%M %p')
	responseDictionary = dict()
	peopleContacted = df['From'].unique().tolist()
	for person in peopleContacted:
	    receivedMessages = df[df['From'] == person]
	    sentMessages = df[df['To'] == person]
	    if (len(sentMessages) == 0 or len(receivedMessages) == 0):
	        # There was no actual conversation
	        continue
	    combined = pd.concat([sentMessages, receivedMessages])
	    combined['Date'] = combined['Date'].apply(dateTimeConverter)
	    combined = combined.sort(['Date'])
	    otherPersonsMessage, myMessage = "",""
	    firstMessage = True
	    for index, row in combined.iterrows():
	        if (row['From'] != personName):
	            if myMessage and otherPersonsMessage:
	                otherPersonsMessage = cleanMessage(otherPersonsMessage)
	                myMessage = cleanMessage(myMessage)
	                responseDictionary[otherPersonsMessage.rstrip()] = myMessage.rstrip()
	                otherPersonsMessage, myMessage = "",""
	            otherPersonsMessage = otherPersonsMessage + row['Content'] + " "
	        else:
	            if (firstMessage):
	                firstMessage = False
	                # Don't include if I am the person initiating the convo
	                continue
	            myMessage = myMessage + str(row['Content']) + " "
	return responseDictionary

def getIosData():
	import pandas as pd
	import sqlite3
	con = sqlite3.connect('3d0d7e5fb2ce288813306e4d4636395e047a3d28')
	messages = pd.read_sql_query('''
		-- more info http://aaron-hoffman.blogspot.com/2017/02/iphone-text-message-sqlite-sql-query.html
		select
		 m.rowid
		,coalesce(m.cache_roomnames, h.id) ThreadId
		,m.is_from_me IsFromMe
		,case when m.is_from_me = 1 then m.account
		 else h.id end as FromPhoneNumber
		,case when m.is_from_me = 0 then m.account
		 else coalesce(h2.id, h.id) end as ToPhoneNumber
		,m.service Service

		/*,datetime(m.date + 978307200, 'unixepoch', 'localtime') as TextDate -- date stored as ticks since 2001-01-01 */
		,datetime((m.date / 1000000000) + 978307200, 'unixepoch', 'localtime') as TextDate /* after iOS11 date needs to be / 1000000000 */

		,m.text MessageText

		,c.display_name RoomName

		from
		message as m
		left join handle as h on m.handle_id = h.rowid
		left join chat as c on m.cache_roomnames = c.room_name /* note: chat.room_name is not unique, this may cause one-to-many join */
		left join chat_handle_join as ch on c.rowid = ch.chat_id
		left join handle as h2 on ch.handle_id = h2.rowid

		where
		-- try to eliminate duplicates due to non-unique message.cache_roomnames/chat.room_name
		(h2.service is null or m.service = h2.service)

		order by
		 2 -- ThreadId
		,m.date
	''', con)
	messages = messages[messages['MessageText'].notnull()]
	messages['MessageText'] = messages['MessageText'].apply(lambda x: x.encode('ascii', errors='ignore')).str.strip()
	messages = messages[messages['MessageText'] != '']
	responseDictionary = {}
	for _, grp in messages.groupby('ThreadId'):
		if len(grp) <= 1:
			continue
		current_from_me = otherPersonsMessage = None
		for _, row in grp.iterrows():
			if current_from_me is not None and row['FromPhoneNumber'] == current_from_phone_number:
				# continue message
				message_parts.append(row['MessageText'])
			else:
				if current_from_me == 1 and otherPersonsMessage is not None:
					myMessage = '. '.join(message_parts).replace('..', '.')
					responseDictionary[otherPersonsMessage] = myMessage
				elif current_from_me == 0:
					otherPersonsMessage = '. '.join(message_parts).replace('..', '.')
				current_from_me = row['IsFromMe']
				current_from_phone_number = row['FromPhoneNumber']
				message_parts = [row['MessageText']]
	return responseDictionary


def cleanMessage(message):
	# Remove new lines within message
	cleanedMessage = message.replace('\n',' ').lower()
	# Deal with some weird tokens
	cleanedMessage = cleanedMessage.replace("\xc2\xa0", "")
	# Remove punctuation
	cleanedMessage = re.sub('([.,!?])','', cleanedMessage)
	# Remove multiple spaces in message
	cleanedMessage = re.sub(' +',' ', cleanedMessage)
	return cleanedMessage

combinedDictionary = {}
if (googleData == 'y'):
	print 'Getting Google Hangout Data'
	combinedDictionary.update(getGoogleHangoutsData())
if (fbData == 'y'):
	print 'Getting Facebook Data'
	combinedDictionary.update(getFacebookData())
if (linkedInData == 'y'):
	print 'Getting LinkedIn Data'
	combinedDictionary.update(getLinkedInData())
if (iosData == 'y'):
	print 'Getting IOS Data'
	combinedDictionary.update(getIosData())
print 'Total len of dictionary', len(combinedDictionary)

print 'Saving conversation data dictionary'
np.save('conversationDictionary.npy', combinedDictionary)

conversationFile = open('conversationData.txt', 'w')
for key,value in combinedDictionary.iteritems():
	if (not key.strip() or not value.strip()):
		# If there are empty strings
		continue
   	conversationFile.write(key.strip() + value.strip())
