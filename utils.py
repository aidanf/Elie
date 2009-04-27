
import os
import sys,string
import config


class logFile:
    """a simple logging class"""
    def __init__(self, filename):
        self.f = open(filename,'a')

    def __del__(self):
        self.f.close()

    def write(msg):
        self.f.write(time.asctime(time.gmtime(time.time()))+"\t"+msg+"\n")

class resultsFile:
    """class for writing results to a file"""
    def __init__(self, filename):
        self.f = open(filename,'w')

    def __del__(self):
        self.f.close()

    def comment(self, msg):
        self.f.write('#'+msg+'\n')

    def write(res,seperator='\t'):
        """writes a tuple to the results file
              res : a tuple containing the results data
        """
        for x in range(len(res)):
            self.f.write(res[x])
            if x < len(res)-1:
                self.write(seperator)
        self.f.write('\n')
        self.f.flush()

def clearDirectory(dirName):
    """deletes all the files in a directory"""
    if not os.path.isdir(dirName):
        raise amException("Directory: "+dirName+" does not exist")
    else:
        files = os.listdir(dirName)
        for f in files:
            os.remove(os.path.join(dirName,f))


def fileList(d,suffix='.elie.pre',list_suffix=0,list_non_suffix=1):
    """return a list of absolute filenames in a directory"""
    #remove any directory names
    files = []
    if not os.path.isdir(d):
        raise str(d)+" is not a directory"
        
    for x in os.listdir(d):
        if list_non_suffix:
            if os.path.isfile(os.path.join(d,x)) and not x[-len(suffix):]==suffix:
                files.append(os.path.join(d,x))
        if list_suffix:
            if os.path.isfile(os.path.join(d,x)) and x[-len(suffix):]==suffix:
                files.append(os.path.join(d,x))
    return files

def log(v,msg,outstream=sys.stderr):
    if v <= config.verbosity:
        outstream.write(msg)
	#outstream.flush()

def arffHeader(fname):
    f = open(fname)
    header = ''
    while 1:
        line = f.readline()
        header.append(line)
        if line[:5] == '@data':
            break
    return header
