#!/usr/bin/python3

import os
import subprocess
import re
import sys
import html.parser
import http.client
import hashlib
import urllib.parse
import gzip
import csv
import json
import collections

tmpPrefix = "/tmp/devjsbuildpy_" + str(os.getuid()) + "_"
print("tmpPrefix=" + tmpPrefix)

def preprocessTemplates():
	print("Preprocessing templates")

	newScriptFiles = []

	templateRoot = root + "/templates/"

	if (not os.path.isdir(templateRoot)):
		print ("No template directory found")
		return

	for (dirPath, dirNames, fileNames) in os.walk(templateRoot):
		for fn in fileNames:
			if (fn.lower().endswith(".html")):
				print("Preprocessing " + fn)

				htmlFn = (dirPath + fn).replace(root + "/", "")
				tmpFile = tmpPrefix + hashlib.sha1(htmlFn.encode("utf-8")).hexdigest() + ".html.cache.js"

				fi = open(dirPath + fn, "r")
				fo = open(tmpFile, "w")

				fo.write('"use strict";\n')
				fo.write('if (typeof(_preloadedTemplateData) == "undefined") var _preloadedTemplateData = {};\n');
				fo.write('_preloadedTemplateData["' + htmlFn + '"] = ' + json.dumps(fi.read()) + ';\n')

				fo.close()
				fi.close()

				newScriptFiles.append(tmpFile)

	return newScriptFiles

def convertCsvToTmpJs(csvFile):
	print("Preprocessing CSV")
	tmpFile = tmpPrefix + hashlib.sha1(csvFile.encode("utf-8")).hexdigest() + ".csv.cache.js"

	m = re.match('.+?/([^/"]+)\.csv', csvFile, re.IGNORECASE)
	keyName = m.group(1)

	print("Converting " + csvFile + " to tmp JS " + tmpFile + ", keyname is " + keyName)

	fi = csv.reader(open(csvFile))

	columnNames = None
	outData = []

	for row in fi:
		if (not columnNames):
			columnNames = row
		else:
			parsedRow = collections.OrderedDict()

			for i in range(len(columnNames)):
				parsedRow[columnNames[i]] = row[i]

			outData.append(parsedRow)


	fo = open(tmpFile, "w")
	fo.write('"use strict";\n')
	fo.write('if (typeof(data) == "undefined") var data = {};\n');
	fo.write('data["' + keyName + '"] = ' + json.dumps(outData, "\t") + ';\n')
	fo.close()

	return tmpFile

def preprocessCsv():
	newScriptFiles = []

	for (dirPath, dirNames, fileNames) in os.walk(root):
		for fn in fileNames:
			if (fn.lower().endswith(".csv")):
				newScriptFiles.append(convertCsvToTmpJs(dirPath + "/" + fn))

	return newScriptFiles

def generateTmpCsvToImpot(importTarget):
	tmpFile = tmpPrefix + hashlib.sha1(importTarget.encode("utf-8")).hexdigest() + ".css.cache.js"
	fo = open(tmpFile, "w")
	fo.write("@import url(" + importTarget + ");\n")
	fo.close()

	return tmpFile

def hashFile(file):
	f = open(file, "rb")

	h = hashlib.sha1()

	for line in f:
		h.update(line + "\n".encode("utf-8"))

	print (file + " ==SHA1=> " + h.hexdigest())

	return h.hexdigest()

def performMinification(command, fileListRaw, ext, indiv=False):

	fileList = []

	overallHash = hashlib.sha1()

	for file in fileListRaw:
		if (file[0:5] == "https"):
			if (ext != "css"):
				pr = urllib.parse.urlparse(file)

				cacheFile = tmpPrefix + hashlib.sha1(file.encode("utf-8")).hexdigest() + ".cache." + ext

				if (not os.path.isfile(cacheFile)):
					print ("Downloading " + file)

					con = http.client.HTTPSConnection(pr.netloc)
					con.request("GET", pr.path)

					respText = con.getresponse().read()

					f = open(cacheFile, "wb")
					f.write(respText)
					f.close()

					print("Downloaded and saved " + str(len(respText)) + " bytes to " + cacheFile)

				file = cacheFile
			else:
				file = generateTmpCsvToImpot(file)
		elif (file[0] != "/"):
			file = root + "/" + file

		if (file):
			fileList.append(file)

			overallHash.update(hashFile(file).encode("utf-8"))
			print("Overall hash: " + str(overallHash.hexdigest()))

	output = ""

	outFileStub = "dist/combined-" + overallHash.hexdigest() + ".min." + ext
	outFileEnd = outFileStub + ".gz"
	outFile = root + "/" + outFileEnd

	if (indiv):
		raise Exception("EX")
	else:
		if ("cleancss" not in command):
			args = [command] + fileList
			print ("args: " + str(args))
			output = subprocess.check_output(args).decode("utf-8")

			f = gzip.open(outFile, "wb")
			f.write(output.encode("utf-8"))
			f.close()
		else:
			args = [command, '-o', root + "/" + outFileStub] + fileList
			print ("args: " + str(args))
			subprocess.check_call(args)

			args = ['gzip', root + "/" + outFileStub]
			print ("args: " + str(args))
			subprocess.check_call(args)


	print("Successfully built " + outFile + " contains " + str(len(output)) + " characters")

	return outFileEnd

root = os.path.dirname(os.path.realpath(sys.argv[1]))

print("Root is " + root)

subprocess.call(["rm", "-rf", root + "/dist"])
subprocess.call(["mkdir", root + "/dist"])

scriptFiles = []
webWorkerScriptFiles = []
cssFiles = []

class CustomHTMLParser(html.parser.HTMLParser):
	def handle_starttag(self, tag, attrs):
		if (tag == "script"):
			src = None
			webWorker = False

			for (k,v) in attrs:
				if (k == "src"):
					src = v
				if (k == "data-webworker"):
					webWorker = True

			if (src):
				scriptFiles.append(src)
				if (webWorker):
					webWorkerScriptFiles.append(src)

		if (tag == "link"):
			href = ""
			isStylesheet = False
			for (k,v) in attrs:
				if (k == "href"):
					href = v
				if (k == "rel" and v == "stylesheet"):
					isStylesheet = True

			if (isStylesheet):
				cssFiles.append(href)
	def handle_endtag(self, tag):
		pass
	def handle_data(self, data):
		pass

parser = CustomHTMLParser()

f = open(sys.argv[1], "r")

for line in f:
	parser.feed(line)

f.close()

print(str(scriptFiles))
print(str(cssFiles))

scriptFiles = preprocessCsv() + scriptFiles
scriptFiles = preprocessTemplates() + scriptFiles

webWorkerOutFile = None

jsOutFile = performMinification('/usr/local/bin/closure-compiler', scriptFiles, 'js')
cssOutFile = performMinification('/usr/local/bin/cleancss', cssFiles, 'css')
if (len(webWorkerScriptFiles) > 0):
	webWorkerOutFile = performMinification('/usr/local/bin/closure-compiler', webWorkerScriptFiles, 'js')

#jsOutFile = "dist/test.js"
#cssOutFile = "dist/test.css"

print(jsOutFile)
print(cssOutFile)

outHtml = open(root + "/index.html", "w")
outHtml.write("<!DOCTYPE HTML>")

class RebuildingHTMLParser(html.parser.HTMLParser):
	def handle_starttag(self, tag, attrs):
		if (tag == "script"):
			return

		if (tag == "link"):
			isStylesheet = False

			for (k,v) in attrs:
				if (k == "rel" and v == "stylesheet"):
					isStylesheet = True

			if (isStylesheet):
				return

		outHtml.write("<" + tag)

		for (k,v) in attrs:
			if (v):
				outHtml.write(' ' + k + '="' + v + '"')
			else:
				outHtml.write(' ' + k)

		if (tag == "link" or tag == "br"):
			outHtml.write("/>")
		else:
			outHtml.write(">")

		if (tag == "head"):
			outHtml.write('<script src="' + jsOutFile + '" async' + ((' data-webworker-src="' + webWorkerOutFile + '"') if webWorkerOutFile else '') + '></script>')
			outHtml.write('<link rel="stylesheet" href="' + cssOutFile + '"/>')
	def handle_endtag(self, tag):
		if (tag != "script" and tag != "link" and tag != "br"):
			outHtml.write("</" + tag + ">")
	def handle_data(self, data):
		outHtml.write(data.strip())

parser = RebuildingHTMLParser()

f = open(sys.argv[1], "r")

for line in f:
	parser.feed(line)

f.close()














