import os
import time
import subprocess
import fileinput



class Synchroniser:
	def __init__(self, projectRootDir):
		self.projectRootDir = projectRootDir
		self.ppSave = self.projectRootDir + "/Configuration/pp_save.cfg"
		self.ppSaveCopy = self.ppSave.replace('.cfg','_copy.cfg')
		self.ppProj = self.projectRootDir + "/Configuration/pp_proj.ini"
		self.cachedTS = os.stat(self.ppSave).st_mtime
		self.globalIncludesReverseList = list()
		self.changes = dict()

		# Make a copy of pp_save for diff purposes
		copyCommand = "cp %s %s" % (self.ppSave,self.ppSaveCopy)
		os.system(copyCommand)

		self.getGlobalIncludesOrder(True)


	def saveDetected(self):
		timeStamp = os.stat(self.ppSave).st_mtime
		if timeStamp != self.cachedTS:
			self.cachedTS = timeStamp
			return True
		else:
			return False

	# Populates self.changes dict with changes variables and values
	def getChangedVariables(self):
		# Clear changes dict
		self.changes = dict()

		# Do a diff between the current pp_save and the old copy
		cmd = "diff %s %s" % (self.ppSave,self.ppSaveCopy)
		diff = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE).stdout.read()

		# Create a list of the changes
		diff = diff.split('\n')
		diff = [d.replace('< ','') for d in diff if '<' in d]

		# Put the changes into self.changes with the variable as the key and the value as the value
		for change in diff:
			variable = change.split('=')[0]
			value = change.split('=')[1]
			self.changes[variable]=value


	# Populates self.globalIncludesReverseList with files in Global Includes in reverse order
	# The reason for the reverse order is due to the later files overwriting the earlier ones
	# on boot
	def getGlobalIncludesOrder(self,local=False):

		self.globalIncludesReverseList = list()
		# Read file into list
		with open(self.ppProj) as f:
			contents = f.readlines()
		
		# Pick out the Global Include files
		for line in contents:
			if "Global Includes" in line:
				self.globalIncludesReverseList.append(line)
				
		# Reverse the list and remove the preceeding fileXX= 
		self.globalIncludesReverseList.reverse()
		self.globalIncludesReverseList = [f.split('=')[1] for f in self.globalIncludesReverseList ]
		self.globalIncludesReverseList = [f.replace('\n','') for f in self.globalIncludesReverseList]
		self.globalIncludesReverseList = [f.replace('\r','') for f in self.globalIncludesReverseList]

		if local:
			self.globalIncludesReverseList = [f.replace('/var/ftp/usrflash/Project',self.projectRootDir) for f in self.globalIncludesReverseList]
		
	# If variable is already declared in Global Include then apply the change there	
	def applyChangeIfExists(self):

		# Read each file
		for pmhFile in self.globalIncludesReverseList:
			with open(pmhFile) as f:
				contents = f.readlines()

			# Check any changes exist in this file
			for key in self.changes.keys():
				matching = [s for s in contents if key in s]
				for m in matching:
					try:
						# Get the index of the last occurance of the variable in the file
						index = len(contents) - 1 - contents[::-1].index(m)
						# Replace
						contents[index]="%s=%s // pp_save.cfg\r\n" % (key,self.changes[key])
					except:
						pass

			with open(pmhFile,'w') as f:
				f.writelines(contents)
			
			
		
			
sync = Synchroniser("/home/lee/work/Project")

while 1:
	time.sleep(1)
	if sync.saveDetected():
		sync.getChangedVariables()
		sync.applyChangeIfExists()