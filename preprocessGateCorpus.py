#!/usr/bin/python

import os,sys,cStringIO
import tagging, config
from xml.parsers import expat

suffix = ".elie.pre"
ignore_tags = {'xml':'','gateapitext':'','docid':'','doc':'', 'text':''}
POSTAGS={'CC':0,
         'CD':0,
         'DT':0,
         'EX':0,
         'FW':0,
         'IN':0,
         'JJ':0,
         'JJR':0,
         'JJS':0,
         'LS':0,
         'MD':0,
         'NN':0,
         'NNS':0,
         'NNP':0,
         'NNPS':0,
         'PDT':0,
         'POS':0,
         'PRP':0,
         'PRP$':0,
         'RB':0,
         'RBR':0,
         'RBS':0,
         'RP':0,
         'SYM':0,
         'TO':0,
         'UH':0,
         'VB':0,
         'VBD':0,
         'VBG':0,
         'VBN':0,
         'VBP':0,
         'VBZ':0,
         'WDT':0,
         'WP':0,
         'WP$':0,
         'WRB':0,}

class stack:
    def __init__(self):
        self.items = []

    def __len__(self):
        return len(self.items)

    def push(self, x):
        self.items.append(x)

    def pop(self):
        if len(self.items) ==0:
            return ''
        else:
            p = self.items[-1]
            self.items = self.items[:-1]
            return p

    def contents(self):
        return self.items

    def clear(self):
        self.items=[]
    
def usage():
    print >>sys.stderr,("%s corpusDirectory fields"%sys.argv[0])



class gateOutputProcesser:
    def __init__(self, annotations):
        self.annotations = {}
        self.toks = []
        self.non_toks = stack()
        for a in annotations:
            self.annotations[a.lower()] = ''
        self.ann_cache = {}
        self.non_ann_cache = {}
        
    def start_element(self,name, attrs):
        name = name.lower()
        attrs['annotations']=[]
        if ignore_tags.has_key(name):
            pass
        elif name=='token' or name=='spacetoken':
            if name == 'spacetoken':
                if self.non_ann_cache.has_key('url'):
                    del self.non_ann_cache['url']
            if name=='spacetoken' and attrs['kind']!='space':
                #print "Space:",name, attrs['kind']
                attrs['string'] = 'xCTRLx'
                attrs['category']=''
                if len(self.toks) > 1 and self.toks[-1]['token']=='xCTRLx': return
            if name=='spacetoken' and attrs['kind']=='space': return
            if name=='token' and attrs['string'] == 'http':
                self.non_ann_cache['url']='url'
            if not tagging.isascii(attrs['string']):
                print "Ignoring NON-ASCII token"
                return
            self.toks.append(self.translate_tok(attrs))
            if self.ann_cache:
                for k in self.ann_cache.keys():
                    attrs['annotations'].append('<'+k.encode('ascii')+'>')
                self.ann_cache = {}
            if self.non_ann_cache:
                for k in self.non_ann_cache.keys():
                    pass
                    #print "NON_ANN",k,"\t",self.non_ann_cache
            #print 'Start',name, str(attrs['string']).encode('ascii'),str(attrs['annotations']).encode('ascii')
        elif self.annotations.has_key(name):
            self.ann_cache[name]=attrs
            #print 'Start',name, attrs
        else:
            self.non_ann_cache[name]=attrs
            #print '\tNONANNStart',name, attrs

    def end_element(self,name):
        name = name.lower()
        if ignore_tags.has_key(name):
            pass
        elif name=='token':
            pass
        elif self.annotations.has_key(name):
            self.toks[-1]['annotations'].append('</'+name.encode('ascii')+'>')
        elif self.non_ann_cache.has_key(name):
            del self.non_ann_cache[name]

    def character_data(self,data):
        pass

    def post_process(self):
        for i in range(len(self.toks)):
            if i == 0:
                for g in self.toks[i]['gaz']:
                    self.toks[i]['erc'].append('s_'+g)
            else:
                for g in self.toks[i]['gaz']:
                    if not g in self.toks[i-1]['gaz']:
                        self.toks[i]['erc'].append('s_'+g)

            if i >= len(self.toks)-2:
                for g in self.toks[i]['gaz']:
                    self.toks[i]['erc'].append('e_'+g)
            else:
                for g in self.toks[i]['gaz']:
                    if not g in self.toks[i+1]['gaz']:
                        self.toks[i]['erc'].append('e_'+g)
        #for t in self.toks:
            #print t['token'],"\t",t['gaz'],"\t",t['erc'],t['types'],t['annotations']

    def translate(self,s):
        p = expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        p.CharacterDataHandler = self.character_data
        p.ParseFile(cStringIO.StringIO(s))
        self.post_process()
        return self.toks

    def translate_tok(self, attrs):
        #not sure how to categorize gate output so we just shove it all into types
        self.atts = {}
        token = attrs['string']
        for r in config.reserved_characters.keys():
            if r in token:
                token = token.replace(r,config.reserved_characters[r])
        for a in attrs:
            self.atts[a]=''
        t = {'token': token.encode('ascii'), 'suffix': '', 'annotations': attrs['annotations'], 'erc': [], 'chunks': [], 'stem': '', 'pos': [], 'types': [], 'gaz': []}
        if POSTAGS.has_key(attrs['category'].encode('ascii')):
            t['pos'] = attrs['category'].encode('ascii')
        if attrs.has_key('orth'): t['types'].append(attrs['orth'].encode('ascii'))
        if attrs.has_key('kind'): t['types'].append(attrs['kind'].encode('ascii'))
        for k in self.non_ann_cache.keys():
            t['gaz'].append(k.encode('ascii'))
        return t
            
if __name__=='__main__':
    try:
        sys.argv[1]
        fields = sys.argv[2:]
        if not fields: raise "Annotations not listed"
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
        g = gateOutputProcesser(fields)
        res = g.translate(open(f).read())
        for r in res:
            print >>prefile,r
        prefile.close()
        count = count-1
