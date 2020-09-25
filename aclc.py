#!/usr/bin/python3

import os
import sys
import string

# argument handling
import argparse
parser = argparse.ArgumentParser()

class Args:
	pass
args = Args()

import codecs
import logging

from datetime import datetime
now = datetime.now()
timestamp = now.strftime("%Y%m%d%H%M%S")

FALSE = 0
TRUE = 1
EOF = -1

statistics = { 
	"filecount": 0,
	"warnings": 0,
	"errors" : 0,
	"linecount": 0
}


find_command = ( 'find . -exec echo {} \\; -exec synoacltool -get {} \\; > %s-aclfile.txt' % (timestamp))


class qacl:

# hier die Methoden und Variablen, um mit dem acl-Listing umzugehen.
# ein ACL-Eintrag sieht folgendermaßen aus:

# ./verzeichnis-groessen.txt
# ACL version: 1 
# Archive: is_inherit,is_support_ACL 
# Owner: [ralf(user)] 
# --------------------- 
#          [0] group:administrators:allow:rwxpdDaARWc--:----  (level:1)
#          [1] group:AndreaRalf:allow:rwxpdDaARWc--:----  (level:1)
#          [2] user:andrea:allow:rwxpdDaARWc--:----  (level:1)

# Die Anzahl der ACL-Einträge ist variabel, das Ende kann man nur daran erkennen, dass eine
# neue PFAD-Zeile beginnt, also mit "./" vom find-Kommando, oder dass die Datei zu Ende ist.
# Die anderen Zeilen kommen so aus synoacltool -get {}.

	names = [
	"path",
	"version",
	"flags",
	"owner",
	"separator"
	]

# hier soll die quell-acl-datei geöffnet werden

	def __init__(self, acllisting):
		#print("__init__")
		self.eof = FALSE
		self.l = ""
		self.aclentry = {}
		self.within = FALSE
		self.acld = open(acllisting,"r")
		self.unread = ""
		self.count = 0
		#if self.acld:
		#	print("Opened ACL-Listing: \"%s\"" % (acllisting))


	def _readlinerstrip(self):
		if self.unread == "":
			#print("_readlinerstrip: calling readline()")
			line = self.acld.readline().rstrip('\n')
		else:
			#print("_readlinerstrip: returning unread line (%s)" % (self.unread))
			line = self.unread
			self.unread = ""
		return line

	def _unreadline(self,line):
		if self.unread != "":
			#print("_unreadline: ERROR: stack full")
			sys.exit(1)
		else:
			self.unread = line

	def _testpath(self):
		#print("_testpath")
		if self.eof:
			raise StopIteration

		self.l = self._readlinerstrip()
		
		if not self.l:
			# da müsste die Datei zu Ende sein, aber eben kein Pfad
			#wir geben trotzdem mal TRUE zurück
			self.eof = TRUE
			return TRUE

		index = self.l.find(".", 0)

		if index == 0:
			# path gefunden, und wir dürfen ihn nur setzen, wenn er nicht schon gesetzt ist!
			savedpath = ""
			try:
				# es gibt schon einen Pfad, d.h., es ist schon der nächste Pfad, pylint liefert unused variable, aber hier provozieren wir einen keyerror!
				# damit wir den allerersten Eintrag nicht verpassen
				savedpath = self.aclentry["path"]
				self._unreadline(self.l)
			except KeyError:
				# damit pylint zufrieden ist wegen savedpath
				index = len(savedpath)
				self.aclentry["path"] = self.l
			
			return TRUE

		return FALSE


	def _readaclentry(self):

		self.count = self.count + 1
		#print("_readaclentry # %10d" % (self.count))

		self.aclentry = {}

		# solange wir noch keinen pfad gefunden haben
		while not self._testpath():
			#print("_readlinerstrip: while not self._testpath()")
			pass

		# jetzt entweder version oder linux mode
		self.l = self._readlinerstrip()
		self.aclentry["version"] = self.l
		if not self.l.__contains__("ACL version"):
			self.aclentry["type"] = "Linuxmode"
			self._testpath()
			return self.aclentry
		else:
			self.aclentry["type"] = "acl"

		# jetzt Archive: is_inherit,is_support_ACL
		self.l = self._readlinerstrip()
		self.aclentry["flags"] = self.l

		# jetzt Owner: [andrea(user)] 
		self.l = self._readlinerstrip()
		self.aclentry["owner"] = self.l

		# jetzt ---------------------
		self.l = self._readlinerstrip()
		self.aclentry["separator"] = self.l

		# jetzt kommen die acls
		while not self._testpath():
			#print("_readaclentry: while not self._testpath() wegen den acls")
			try:
				self.aclentry["acl"].append(self.l)
			except KeyError:
				self.aclentry["acl"] = [self.l]

		# wenn wir hier wieder rauskommen, dann haben wir eine Pfadzeile gelesen
		# und die ist auch schon wieder "ungelesen" worden, damit wir beim nächsten Aufruf wieder
		# reinkommen

		return self.aclentry

	def __iter__(self):
		#print("__iter__")
		#self.aclentry = self._readaclentry()
		return self

	def __next__(self):
		#a = self.aclentry
		#print("__next__a = \"%s\"" % (a))
		self.aclentry = self._readaclentry()
		if self.aclentry != {}:
			return self.aclentry
		else:
			raise StopIteration


def path_singlequote(p):
	# put path in singlequotes and quote single quotes
	# '"'"'
	n = p.replace("'","'\"'\"'")
	n = "'" + n + "'"
	return n

def print_acle(x):
	print("%s" % x["path"])
	try:
		print("%s" % x["version"])
		print("%s" % x["flags"])
		print("%s" % x["owner"])
		print("%s" % x["separator"])
		for d in x["acl"]:
			print("%s" % d)
	except KeyError:
		pass

def gen_sh_commands(x):

	acllevels = []

	# für "." generieren wir kein Kommando
	if x["path"] == ".":
		return

	try:
		pass
	except KeyError:
		print("# skipping Linux mode: %s" % (x["path"]))
		return


	singlequoted_path = path_singlequote(x["path"])
	
	print("echo %s" % (singlequoted_path))
	
	# erstmal die acls löschen
	print("synoacltool -del %s" % (singlequoted_path))

	#synoacltool -set-archive PATH [ACL Archive Option]
	i = x["flags"].split()
	print("synoacltool -set-archive %s '%s'" % (singlequoted_path, i[1]))
	has_ACL = i[1].__contains__("has_ACL")

	# und es gibt noch diesen Fall:
	# [0] user:admin:allow:rwxpdDaARWcCo:fd--  (level:1)
	# [1] group:administrators:allow:rwxpdDaARWc--:fd--  (level:2)
	# hier gibt es trotz is_inherit noch einen echten nicht vererbten Eintrag mit level:1
	# frage ist wie erkennt man die echten von den geerbten einträgen?
	# wir kucken mal die levels an, wenn die nicht alle gleich sind, dann sind die niedrigeren vermutlich echte
	# level:0 sind auf jeden Fall echte


	#synoacltool -set-owner PATH [user|group] NAME, i.e. Owner: [ralf(user)]
	i = x["owner"].split('[')
	j = i[1].split('(')
	owner = j[0]
	# group = j[1].rstrip(')] ')
	print("synoacltool -set-owner %s user '%s'" % (singlequoted_path, owner))

	# first pass, um herauszufinden, welches die echten Einträge sind
	for d in x["acl"]:
		#	 [0] group:administrators:allow:rwxpdDaARWc--:----  (level:0)
		i = d.split()
		level = int(i[2].split(':')[1].rstrip(')'))
		acllevels.append(level)

	minlevel = min(acllevels)
	maxlevel = max(acllevels)

	setacl = -1
	difflevel = maxlevel - minlevel
	if difflevel == 0:
		# alle gleich, dann könnten sie vererbt sein, es sei denn, der level ist 0
		if maxlevel == 0:
			setacl = 0
	else:

		if has_ACL:
			setacl = minlevel

		if difflevel != 1:
			statistics["warnings"] = statistics["warnings"] + 1
			logging.warning("ACL Levels differ by more than one!!!!")
			logging.warning("%s" % (x["path"]))
			try:
				logging.warning("%s" % x["version"])
				logging.warning("%s" % x["flags"])
				logging.warning("%s" % x["owner"])
				logging.warning("%s" % x["separator"])
				for d in x["acl"]:
					logging.warning("%s" % d)
			except KeyError:
				pass


	# und jetzt die commands erzeugen für die echten, die mit dem minlevel
	number = 0
	for d in x["acl"]:
		#	 [0] group:administrators:allow:rwxpdDaARWc--:----  (level:0)
		i = d.split()
		if acllevels[number] == setacl:
			print("synoacltool -add %s '%s'" % (singlequoted_path, i[1]))
		number = number + 1


def gen_check_commands(x):

	singlequoted_path = path_singlequote(x["path"])
	print("echo %s" % (singlequoted_path))
	print("synoacltool -get %s" % (singlequoted_path))



def do():

	if args.show_find_command:
		print("%s" % (find_command))
		return

	reproduce = TRUE

	print_header = TRUE

	try:
		aclo = qacl(args.inputfile)
	except (AttributeError, TypeError) as e:
		logging.warning("inputfile missing (use -i inputfile)")
		return

	for x in aclo:

		statistics["filecount"] = statistics["filecount"] + 1

		if args.gen_sh_commands:
			if print_header:
				print_header = FALSE
				print("#!/bin/bash")
				print("set -o histexpand")
				print("# %s" % (timestamp))
				print("# shell commands to set the ACLs via synoacl")

			gen_sh_commands(x)
			reproduce = FALSE

		if args.gen_check_commands:
			if print_header:
				print_header = FALSE
				print("#!/bin/bash")
				print("set -o histexpand")
				print("# %s" % (timestamp))
				print("# shell commands to get all the ACLs via synoacl in order to diff them against the original ACLs, diff should show no differences")
			gen_check_commands(x)
			reproduce = FALSE

		if reproduce:
			print_acle(x)

def do_args():
	parser.add_argument(
		'-d', '--debug',
		help="Print lots of debugging statements",
 		action="store_const", dest="loglevel", const=logging.DEBUG,
		default=logging.WARNING,
	)

	parser.add_argument("-s", "--show_find_command", help="show find command to generate acl file on synology", action="store_true")

	parser.add_argument(
		'-v', '--verbose',
		help="Be verbose",
		action="store_const", dest="loglevel", const=logging.INFO,
	)

	parser.add_argument("-i", "--inputfile", help="otional inputfile")
	# parser.add_argument("aclfile", help="filename of acl file listing")
	parser.add_argument("-g", "--gen_sh_commands", help="generate shell commands", action="store_true")
	parser.add_argument("-c", "--gen_check_commands", help="generate shell commands for checking", action="store_true")

	parser.parse_args(namespace=args)
	pass


def do_logging():
	logging.basicConfig(stream=sys.stderr, level=args.loglevel, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def main():
	

	do_args()

	do_logging()

	do()

	logging.info("%d files" % statistics["filecount"])
	if statistics["errors"] != 0:
		logging.warning("%d errors" % statistics["errors"])

if __name__=='__main__':
    main()
