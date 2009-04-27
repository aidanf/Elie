#!/usr/bin/python

import os,sys
import tagging

suffix = ".elie.pre"

def usage():
    print >>sys.stderr,("%s corpusDirectory"%sys.argv[0])
"""    
try:
    if os.path.isfile(sys.argv[1]):
        files = list(sys.argv[1])
    else:
        files = os.listdir(sys.argv[1])
        outdir = sys.argv[1]
        if outdir[-1] == '/':
           outdir = outdir[-1]
        outdir = outdir + '.preprocessed'
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
except:
    print "Error:",str(sys.exc_info()[0])
    usage()
    sys.exit()
"""
try:
    sys.argv[1]
except:
    usage()
    sys.exit()
outdir = ''
if os.path.isfile(sys.argv[1]):
    files = [sys.argv[1]]
else:
    files = os.listdir(sys.argv[1])
    outdir = sys.argv[1]
    if outdir[-1] == '/':
        outdir = outdir[:-1]
    outdir = outdir + '.preprocessed'
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    for i in range(len(files)):
        files[i] = os.path.join(sys.argv[1],files[i])
        if files[i][-len(suffix):]==suffix:
            files[i]='DELETE_ME'
    while 'DELETE_ME' in files:
        files.remove('DELETE_ME')

count = len(files)
print count,"files to process..."
for f in files:
    if outdir:
        prefile = open(os.path.join(outdir,os.path.split(f)[-1]+suffix),'w')
    else:
        prefile = open(f+suffix,'w')
    print count,"processing: ",f
    g = tagging.IEtagger()
    try:
        pass
        res = g.tag(open(f).read())
    except tagging.TaggingError:
        print >>sys.stderr,"""ERROR processing %s
        Possible problems:
        control characters:
        words containing more than one dash
        e.g. x-host-header -> xhost-header
        """ % (f)

        sys.exit()
    for r in res:
        print >>prefile,r
    prefile.close()
    count = count-1
    #raw_input()
