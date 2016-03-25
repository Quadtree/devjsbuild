#!/usr/bin/python3

import os
import subprocess
import re

def performMinification(command, srcDirs, ext, indiv=False):
	fileList = []
	for srcDir in srcDirs:
		for dirRoot, dirs, files in os.walk(root + "/" + srcDir):
			for file in files:
				if (file.endswith(ext)):
					fileList.append(dirRoot + "/" + file)

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

	f = open(root + "/dist/sbcrs1-calc.min." + ext, "w")
	f.write(output)
	f.close()

root = os.path.dirname(os.path.realpath(__file__))

print("Root is " + root)

subprocess.call(["rm", "-rf", root + "/dist"])
subprocess.call(["mkdir", root + "/dist"])

performMinification('closure-compiler', ['js', 'kickstart'], 'js')
performMinification('yui-compressor', ['css', 'kickstart'], 'css', True)