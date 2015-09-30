#!/usr/bin/env python
#coding: utf-8
import praw
import OAuth2Util
import os
import pickle
import re
import requests
from BeautifulSoup import BeautifulSoup

class DESTINY():
	def __init__(self, subreddit):
		self.path = os.path.realpath(__file__)
		self.path = self.path.replace(os.path.basename(__file__), "")
		self.r = praw.Reddit("/r/FlawlessRaiders card checker v0.1")
		self._o = OAuth2Util.OAuth2Util(self.r, configfile=self.path+"oauth.txt")
		self.reg = re.compile(r"GT ?: ?(\w+)", flags=re.IGNORECASE)
		self.subreddit = self.r.get_subreddit(subreddit)

		try:
			with open(self.path+"doneposts", "rb") as file:
				self.doneposts = pickle.load(file)
		except IOError:
			with open(self.path+"doneposts", "wb") as file:
				pickle.dump([], file)
			self.doneposts = []

	def checkCard(self, gamertag):
		req = requests.get("http://destinytracker.com/destiny/grimoire/ps/{}".format(gamertag))
		if "Can't find any stats for" in req.text:
			req = requests.get("http://destinytracker.com/destiny/grimoire/xbox/{}".format(gamertag))
			if "Can't find any stats for" in req.text:
				return None
		soup = BeautifulSoup(req.content)

		oryxdefeated = soup.find("a", {"href": "//db.destinytracker.com/grimoire/enemies/exalted-hive/oryx-defeated"})
		if oryxdefeated.parent.parent['class'] == "acquired":
			return True
		return False

	def parse(self):
		for i in self.subreddit.get_comments():
			result = self.reg.findall(i.body)
			if i.id in self.donepost:
				continue
			if not result:
				#self.doneposts.append(i.id)
				continue
			card = self.checkCard(result[-1])
			i.reply("Killed Oryz?: {}".format("Yes" if card is True else "No"))
			self.doneposts.append(i.id)
			self.save()
		for i in self.subreddit.get_new():
			if not i.selftext:
				self.doneposts.append(i.id)
				continue
			if i.id in self.donepost:
				continue
			result = self.reg.findall(i.selftext)
			if not result:
				self.doneposts.append(i.id)
				continue
			card = self.checkCard(result[-1])
			i.add_comment("Killed Oryz?: {}".format("Yes" if card is True else "No"))
			self.doneposts.append(i.id)
			self.save()

	def save(self):
		with open(self.path+"doneposts", "wb") as file:
			pickle.dump(self.doneposts, file)

if __name__ == "__main__":
	d = DESTINY("")
	d.parse()