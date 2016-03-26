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
			
				cacheFile = "/tmp/" + hashlib.sha1(file.encode("utf-8")).hexdigest() + ".cache." + ext
				
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
				file = None
		else:
			file = root + "/" + file
		
		if (file):
			fileList.append(file)
			
			overallHash.update(hashFile(file).encode("utf-8"))
	
	output = ""
	
	outFileStub = "dist/combined-" + overallHash.hexdigest() + ".min." + ext
	outFileEnd = outFileStub + ".gz"
	outFile = root + "/" + outFileEnd
	
	if (indiv):
		raise Exception("EX")
	else:
		if (command != "cleancss"):
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

jsOutFile = performMinification('closure-compiler', scriptFiles, 'js')
cssOutFile = performMinification('cleancss', cssFiles, 'css')

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
			isExternal = False
		
			for (k,v) in attrs:
				if (k == "rel" and v == "stylesheet"):
					isStylesheet = True
				if (k == "href" and v[:5] == "https"):
					isExternal = True
					
			if (isStylesheet and not isExternal):
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
			outHtml.write('<script src="' + jsOutFile + '" async></script>\n')
			outHtml.write('<link rel="stylesheet" href="' + cssOutFile + '"/>\n')
	def handle_endtag(self, tag):
		if (tag != "script" and tag != "link" and tag != "br"):
			outHtml.write("</" + tag + ">")
	def handle_data(self, data):
		outHtml.write(data)

parser = RebuildingHTMLParser()
		
f = open(sys.argv[1], "r")

for line in f:
	parser.feed(line)
	
f.close()














