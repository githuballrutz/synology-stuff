#!/usr/bin/python3

import os
import sys
import string
import argparse
import codecs

FALSE = 0
TRUE = 1

MAXLENGTH = 143
histogram = {}
command = FALSE

def do(dateiname, maxlength, gencom):

	#print("do(%s, %s)" % (dateiname, maxlength))
	#sys.exit(1)

	count = 0
	tc = 0
	accumulatedpercentage = 0

	d = open(dateiname,"r")
	for l in d:
		ls = l.rstrip('\n')
		dirbase = os.path.split(ls)
		zfl = len(dirbase[1])
		fl = len(dirbase[1].encode('utf-8'))
		# if fl != zfl:
		# 	print("fl != zfl: %d != %d (%s)" % (fl, zfl, dirbase[1]))

		try:
			histogram[fl] = histogram[fl] + 1
		except KeyError:
			histogram[fl] = 1
		if fl > maxlength:
			if gencom:
				print("# maxlength (%d) exceeded %d: [%s] \"%s\"" % (maxlength, fl, dirbase[0], dirbase[1]))
				print("cd \'%s\' && mv \'%s\' \'%s\' && cd -" % (dirbase[0], dirbase[1], dirbase[1]))
			else:
				print("maxlength (%d) exceeded %d: [%s] \"%s\"" % (maxlength, fl, dirbase[0], dirbase[1]))
			count = count + 1

	if count == 1:
		fs = "file"
	else:
		fs = "files"

	print("** Results ***")
	print("%d %s exceeded maxlength (%d)" % (count, fs, maxlength))

	# print("*** Histogram ***")
	# for key in sorted(histogram.keys()):
	# 	print("%4d: %10d" % (key, histogram[key]))
	# 	tc = tc + histogram[key]
	# 	#key=operator.itemgetter(1),reverse=True)
	# print("*** Ranking ***")
	# for key, value in sorted(histogram.items(), key=lambda item: item[1],reverse=True):
	# 	percentage = value*100/tc
	# 	accumulatedpercentage = accumulatedpercentage + percentage
	# 	print("%4d: %10d (%10.6f%%) (%10.6f%%)" % (key, value, percentage, accumulatedpercentage) )
		

	print("total files: %10d" % (tc))

	d.close()


def usage():
    print('''Usage: %s [dateiname]''' % (os.path.basename(sys.argv[0])))


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("file", help="filename of file listing")
	parser.add_argument("-m", "--maxlength", help="set maxlength", type=int, default=MAXLENGTH)
	parser.add_argument("-c", "--command", help="generate sh-commands", action="store_true")
	args = parser.parse_args()
	command = args.command

	do(args.file, args.maxlength, command)


if __name__=='__main__':
    main()