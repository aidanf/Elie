#!/usr/bin/python

import sys,os,re

def usage():
    print "Usage: %s docDir fields..." % sys.argv[0]

def start_element(name,attrs):
    print

try:
    docsDir = sys.argv[1]
    fields = sys.argv[2:]
except:
    usage()
    sys.exit()

stats = {}
stats['files'] = 0
for fld in fields:
    stats[fld] = 0


files = os.listdir(docsDir)
for i in range(len(files)):
    files[i] = os.path.join(docsDir,files[i])
for f in files:
    stats['files'] = stats['files']+1
    print f
    txt = open(f).read()
    for fld in fields:
        patt = '<'+fld+r'>((.|\n)*?)</'+fld+'>'
        all = re.findall(patt,txt)
        print fld," : ",
        for a in all:
            print a[0],' : ',
            stats[fld] = stats[fld]+1
        print
    print

print "\nStats"
for k in stats.keys():
    print k, stats[k]
