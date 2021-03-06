#!/usr/bin/env python
#coding: utf-8
import praw
import OAuth2Util
import os
import gspread
import json
from oauth2client.client import SignedJwtAssertionCredentials
import re
import pickle

class MMABOT():
	def __init__(self, subreddit, apijson, spreadsheetkey):
		self.path = os.path.realpath(__file__)
		self.path = self.path.replace(os.path.basename(__file__), "")
		self.r = praw.Reddit("/r/MMA Stats bot v0.2")
		self._o = OAuth2Util.OAuth2Util(self.r, configfile=self.path+"oauth.txt")
		self.subreddit = self.r.get_subreddit(subreddit)

		try:
			with open(self.path+"doneposts", "rb") as file:
				self.doneposts = pickle.load(file)
		except (IOError, EOFError) as e:
			with open(self.path+"doneposts", "wb") as file:
				pickle.dump([], file)
			self.doneposts = []

		self.reg = re.compile(r"!pickem (\S*)", flags=re.IGNORECASE)
		self.template = """Stats as of *{}*|/u/{}
:|:
Current P4P Ranking|{}
Current Weight Class|{}
Weight Class Ranking|{}
Overall Picks|{}
Pick Accuracy|{}"""


		json_key = json.load(open(apijson))
		credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), ['https://spreadsheets.google.com/feeds'])
		self.gc = gspread.authorize(credentials)
		self.spreadsheet = self.gc.open_by_key(spreadsheetkey)
		self.abbrev = {"Heavyweight": "HW", "Light Heavyweight": "LHW", "Middleweight": "MW", "Lightweight": "LW", "Featherweight": "FTW", "Bantamweight": "BW", "Flyweight": "FLW", "Women's Bantamweight": "WBW", "Women's Strawweight": "WSW", "Welterweight": "WW"}

		self.eventtitle = self.spreadsheet.get_worksheet(0).title

	def gatherValues(self, username):
		worksheet = self.spreadsheet.worksheet("P4P")
		result = {}

		values_list = worksheet.col_values(4)
		cells = worksheet.findall("/u/{}".format(username))

		if not cells:
			print username
			return False

		for i in cells:
			if i.col == 4:
				result['weightclass'] = worksheet.cell(i.row, 5).value
				result['p4pranking'] = worksheet.cell(i.row, 1).value

		worksheet = self.spreadsheet.worksheet(self.abbrev[result['weightclass']])
		cell = worksheet.find("/u/{}".format(username))
		result['weightclassranking'] = worksheet.cell(cell.row, 1).value
		result['totalpicks'] = "{}/{}".format(worksheet.cell(cell.row, 6).value, worksheet.cell(1, 6).value)
		result['pickaccuracy'] = worksheet.cell(cell.row, 8).value

		return result

	def save(self):
		with open(self.path+"doneposts", "wb") as file:
			pickle.dump(self.doneposts, file)

	def createResponse(self, username):
		response = self.template
		values = self.gatherValues(username)
		if values is False:
			return False
		return response.format(self.eventtitle,\
		 username, \
		 values['p4pranking'], \
		 values['weightclass'], \
		 values['weightclassranking'], \
		 values['totalpicks'], \
		 values['pickaccuracy'])

	def parseComments(self):
		for post in self.r.search("[Official] /r/MMA Pick 'Em Tournament:", self.subreddit):
			for i in praw.helpers.flatten_tree(post.comments):
				if i.id in self.doneposts:
					continue
				try:
					username = self.reg.match(i.body).group(1)
				except AttributeError:
					self.doneposts.append(i.id)
					print "AttributeError"
					self.doneposts.append(i.id)
					self.save()
					continue
				
				response = self.createResponse(username)
				if response is not False:
					i.reply(response)
				self.doneposts.append(i.id)
				self.save()