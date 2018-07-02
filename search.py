#!/usr/bin/python
# Lee Vanrell 7/1/18

def main():
	print "\n==========Beginning Pgm===============\n"
	print "Loading Words from %s" % Word_file

	Primary_words, Secondary_words = getWords()
	Secondary_words_count = len(Secondary_words)

	print "\tPrimary: %s" % Primary_words
	print "\tSecondary: %s" % Secondary_words
	print "Loading Filetypes from %s" % Filetypes_file

	FileTypes = readFile(Filetypes_file)

	print "\tFiles: %s" % FileTypes

	BaseQuery = str(" ".join(str(x) for x in Primary_words))
	if use_blacklist:
		Queries = filterQueries(getQueries(BaseQuery, Secondary_words, Secondary_words_count), readFile(Blacklist_file))
	else:
		Queries = getQueries(BaseQuery, Secondary_words, Secondary_words_count)
	
	print "\n==========Beginning Searches==========\n"
	Websites = set(getWebsites(Queries, FileTypes))
	Screens, Downloads = sortWebsites(Websites, FileTypes)
	print "\n==========Beginning Downloads=========\n"
	print "\t Attempting to Download From %s URLs" % len(Downloads)
	Errors = getDownloads(Downloads)
	if use_screens:
		print "\t Attempting to take %s Screenshots" % (len(Screens) + (len(Errors)))
		getScreens(Screens, Errors)
	print '\n Finished..'

def getWords(): 
	Primary_words = []
	Secondary_words = []
	File_types = []
	with open(Word_file) as f:
		lines = f.readlines()
		lines = [x.strip() for x in lines]
		for line in lines:
			if '*' in line:
				Primary_words.append(line.replace('*', ''))
			else:
				Secondary_words.append(line)
	return Primary_words, Secondary_words

def readFile(file_path):
	if not os.path.exists(file_path):
		open(file_path, 'w')
	with open(file_path, 'r+') as f:
		file = f.readlines()
		file = [x.strip() for x in file]
	return file

def getQueries(base_query, secondary_words, secondary_words_count): 
	queries = []
	for x in range(1, secondary_words_count + 1):
		queries.extend([base_query + " " + s for s in[" ".join(term) for term in combinations(secondary_words, x)]])
	return queries

def filterQueries(queries, blacklist):
	return [x for x in queries if x not in blacklist]

def getWebsites(queries, filetypes):
	websites = []
	file = "log.txt"
	for query in queries:
		print "Searching google with query: %s" % query 
		print "\t No file filter"
		websites.extend(googleSearch(query))
		if use_filter:
			for file in filetypes:
				print "\t Filtering for .%s" % file
				websites.extend(googleSearch(file + " " +  query))
		appendFile(websites, file)
		if use_blacklist:
			print "\t Appending Query to Blacklist"
			appendBlacklist(query)
	return websites

def googleSearch(query):
	top_results = []
	for j in search(query, tld="co.in", num=Number_of_results, stop=1, pause=2):
		top_results.append(j)
	return top_results

def appendFile(data, file_path):
	if not os.path.exists(file_path):
		open(file_path, 'w')
	with open(file_path, 'a') as f:
		[f.write(line+ '\n') for line in data]

def sortWebsites(urls, filetypes):
	downloads = []
	screens = []
	for url in urls:
		if any(ext in url for ext in filetypes):
			downloads.append(url)
		else:
			screens.append(url)
	return screens, downloads


def getDownloads(downloads):
	errors = []
	dl_count = 0 
	err_count = 0
	total_files = len(downloads)
	for url in downloads:
		file_name = url.split('/')[-1]
		if url.split('.')[-1] != 'com':
			folder = 'downloads/' + url.split('.')[-1] + '/'
		else:
			file_path = 'downloads/unknown'
		file = folder + file_name

		if not os.path.exists(folder):
			os.makedirs(folder)
		if not os.path.exists(file):
			try:
				data = urllib2.urlopen(url)
				write = data.read()
				with open(file, 'wb') as f:
					f.write(write)
			except Exception as e:
				print "\tError with downloading %s: %s" % (url, e)
				errors.append(url)
		else:
			dl_count += 1
	print "\n\tFailed Downloading From %s URLs" % err_count
	return errors

def getScreens(screens, errors):
	folder = './downloads/screenshots/'
	file = folder + 'screenshot_list.txt'
	makeScreenlist(screens, errors, folder, file)
	print 'webscreenshot -o %s -i %s' % (folder, file)

def makeScreenlist(screens, errors, folder, file):
	if not os.path.exists(folder):
		os.makedirs(folder)
	with open(file, 'w') as f:
		[f.write(url + '\n') for url in screens]
		[f.write(url + '\n') for url in errors]

def appendBlacklist(line):
	with open(Blacklist_file, 'a') as f:
		[f.write(line+ "\n")]

if __name__ == '__main__':
	import sys
	import os
	from subprocess import call
	if not os.geteuid() == 0:
		print('\nscript must be run as root!\n')
		sys.exit(1)
	try:
		from itertools import combinations
		from itertools import imap
	except ImportError:
		print "\nError importing intertools\n"
		sys.exit(1)
	try:
		from googlesearch import search
	except ImportError:
		print "\nError importing google\n"
		sys.exit(1)
	try: 
		import urllib2
	except ImportError:
		print "\nError importing urrlib2\n"
		sys.exit(1)

	try:
		import argparse
	except ImportError:
		print "\n Error importing argparse"

	parser = argparse.ArgumentParser(description='google-term-scraper')
	parser.add_argument('-nB', '--no_blacklist', default=False, dest='no_blacklist', action='store_true', help='will not use a blacklist to filter already used searches')
	parser.add_argument('-nF', '--no_filter_files', default=False, dest='no_filter_files', action='store_true', help='will not use filefilter: search engine option')
	parser.add_argument('-nS', '--no_screenshots', default=False, dest='no_screenshots', action='store_true')
	parser.add_argument('-wF', '--words_file', default='words.txt', help='specify the file location of word list' )
	parser.add_argument('-fF', '--filetype_file', default='filetypes.txt', help='specify the file location of filetype list')
	parser.add_argument('-bF', '--blacklist_file', default='blacklist.txt', help='specify the file location of black list')   
	parser.add_argument('-R', '--results', default=10, help='number of top results collected in google search')
	args = parser.parse_args()

	Word_file = args.words_file
	Filetypes_file = args.filetype_file
	Blacklist_file = args.blacklist_file
	Number_of_results = args.results
	use_blacklist = not args.no_blacklist
	use_filter = not args.no_filter_files
	use_screens = not args.no_screenshots

	args = parser.parse_args()
	main()