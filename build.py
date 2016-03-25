#!/usr/bin/python3

import os
import subprocess
import re
import sys
import html.parser
import http.client
import hashlib
import urllib.parse

def scanForInDirectory():
	fileList = []
	for srcDir in srcDirs:
		for dirRoot, dirs, files in os.walk(root + "/" + srcDir):
			for file in files:
				if (file.endswith(ext)):
					fileList.append(dirRoot + "/" + file)

	output = ""


def performMinification(command, fileListRaw, ext, indiv=False):

	fileList = []

	for file in fileListRaw:
		
	
		if (file[0:5] == "https"):
			pr = urllib.parse.urlparse(file)
		
			cacheFile = "/tmp/" + hashlib.sha1(file.encode("utf-8")).hexdigest() + ".cache." + ext
			fileList.append(cacheFile)
			
			if (not os.path.isfile(cacheFile)):
				print ("Downloading " + file)
				
				con = http.client.HTTPSConnection(pr.netloc)
				con.request("GET", pr.path)
				
				respText = con.getresponse().read()
				
				f = open(cacheFile, "wb")
				f.write(respText)
				f.close()
				
				print("Downloaded and saved " + str(len(respText)) + " bytes to " + cacheFile)
			
		else:
			fileList.append(root + "/" + file)
	
	output = ""
	
	if (indiv):
		for file in fileList:
			args = [command] + [file]
			print ("args: " + str(args))
			output += subprocess.check_output(args).decode("utf-8") + "\n"
	else:
		args = [command] + fileList
		print ("args: " + str(args))
		output = subprocess.check_output(args).decode("utf-8")

	if (ext == "css"):
		output = re.sub("@import[^;]+;", "", output)

	outFile = root + "/dist/built" + hashlib.sha1(output.encode("utf-8")).hexdigest() + ".min." + ext
		
	f = open(outFile, "w")
	f.write(output)
	f.close()
	
	print("Successfully built " + outFile + " contains " + str(len(output)) + " characters")

root = os.path.dirname(os.path.realpath(sys.argv[1]))

print("Root is " + root)

subprocess.call(["rm", "-rf", root + "/dist"])
subprocess.call(["mkdir", root + "/dist"])

scriptFiles = []
cssFiles = []

class CustomHTMLParser(html.parser.HTMLParser):
	def handle_starttag(self, tag, attrs):
		if (tag == "script"):
			for (k,v) in attrs:
				if (k == "src"):
					scriptFiles.append(v)
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

performMinification('closure-compiler', scriptFiles, 'js')
performMinification('yui-compressor', cssFiles, 'css', True)














