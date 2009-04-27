#!/usr/bin/python

import sys, string, shlex, StringIO, os, glob, unicodedata, re, tempfile, popen2
import config
import porterstemmer

TaggingError = "TaggingError"

def usage():
    print >>sys.stderr,("%s file"%sys.argv[0])


def _ctoi(c):
    """returns character ascii"""
    if type(c) == type(""):
        return ord(c)
    else:
        return c

class IEtokeniser:
    def __init__(self,s):
        s = string.replace(s,'<',' <')
        s = string.replace(s,'>','> ')        
        #s = self._preprocess(s)
        self._t = shlex.shlex(StringIO.StringIO(s))
        self._t.wordchars = self._t.wordchars+'</>-'
        self._t.quotes = ''
        self._t.commenters = ''
        self._tokens = []
        while 1:
            tok = self._t.get_token()
            tmp = []
            if not tok:
                break
            #split also numbers and letters : numbers and hyphen
            """
            if '-' in tok:
                tmp = tok.split('-')
                if isDigits(tmp[0]) or isDigits(tmp[1]):
                    tmp.insert(1,'-')
                else:
                    tmp = []
            """
            if lettersDigits(tok):
                tmp = [tok[0],'']
                count = 0
                for c in tok[1:]:
                    if isDigits(c) != isDigits(tmp[count]):
                        count = count + 1
                        if count >= len(tmp):
                            tmp.append('')
                    tmp[count] = tmp[count] + c
                print "XXX",tmp
            if not tmp:
                self._tokens.append(tok)
            else:
                self._tokens = self._tokens + tmp
        self.index=0
        
    def next(self):
        ret = ''
        if self.index >= len(self._tokens):
            pass
        else:
            ret = self._tokens[self.index]
            self.index = self.index + 1
        return ret

    def _preprocess(self,s):
        subs = {}
        rex_file = open('tokeniser.subs')
        for line in rex_file:
            rex, sub = line.split('=')
            subs[rex.strip()] = sub.strip()
        for s in sub:
            print "XXX",s,sub[s]
        
def testIEtokeniser(s):
    t = IEtokeniser(s)
    while 1:
        token = t._t.get_token()
        if not token:
            break
        print token
    print
    print t._t.commenters
    print t._t.wordchars
    print t._t.quotes




class stopGaz:
    def __init__(self,stopfilename=os.path.join(config.basedir,'data','stopwords.txt')):
        self._stopwords={}
        sf = open(stopfilename)
        while 1:
            stopword = string.lower(string.strip(sf.readline()))
            if not stopword:
                break
            self._stopwords[stopword] = 1

    def search(self,token):
        return self._stopwords.has_key(string.lower(token))

class dictGaz(stopGaz):
    def __init__(self):
        stopGaz.__init__(self,stopfilename=os.path.join(config.basedir,'data','words.list'))


class nameGaz:
    def __init__(self,last=os.path.join(config.basedir,'data','dist.all.last'),firstmale=os.path.join(config.basedir,'data','dist.male.first'),firstfemale=os.path.join(config.basedir,'data','dist.female.first')):
        self.last={}
        self.firstm={}
        self.firstf={}

        f = open(last)
        while 1:
            line = f.readline()
            if not line:
                break
            tmp = string.split(line)
            n,r = tmp[0],tmp[3]
            self.last[string.lower(n)]=r

        f = open(firstmale)
        while 1:
            line = f.readline()
            if not line:
                break
            tmp = string.split(line)
            n,r = tmp[0],tmp[3]
            self.firstm[string.lower(n)]=r

        f = open(firstfemale)
        while 1:
            line = f.readline()
            if not line:
                break
            tmp = string.split(line)
            n,r = tmp[0],tmp[3]
            self.firstf[string.lower(n)]=r

    def search(self,s):
        """returns a tuple with search results for (lastname, firstname_male, firstname_female)"""
        ret = []
        if self.last.has_key(string.lower(s)):
            ret.append('person_last')
        if self.firstm.has_key(string.lower(s)):
            ret.append('male')
            if not 'person_first' in ret:
                ret.append('person_first')
        if self.firstf.has_key(string.lower(s)):
            ret.append('female')
            if not 'person_first' in ret:
                ret.append('person_first')
        return tuple(ret)


def test_nameGaz():
    n = nameGaz()
    while 1:
        print "???- ",
        name = string.strip(raw_input())
        if not name:
            break
        print n.search(name)

def isDigits(s):
    match=string.digits
    for letter in s:
        if letter not in match:
            return None
    return 1
    
def isPrintable(s):
    match=string.digits + string.letters + string.punctuation
    for letter in s:
        if letter not in match:
            return None
    return 1

def allUpper(s):
    match=string.uppercase
    for letter in s:
        if letter not in match:
            return None
    return 1
def allLower(s):
    match=string.lowercase
    for letter in s:
        if letter not in match:
            return None
    return 1

def allLetters(s):
    match=string.letters
    for letter in s:
        if letter not in match:
            return None
    return 1

def lettersDigits(s):
    match=string.digits + string.letters
    letters = 0
    digits = 0
    for letter in s:
        if letter not in match:
            return None
        if letter in string.letters:
            letters = 1
        elif letter in string.digits:
            digits = 1
    return letters and digits
    
def isascii(s, match = re.compile("^[\0-\177]+$").match) :
    return match(s) >= 0

def isword(s):
    s = string.strip(s)
    if allLetters(s):
        return 1
    elif '-' in s:
        l,r = string.split(s,'-')[0],string.split(s,'-')[1]
        if allLetters(l) and allLetters(r):
            return 1
    return None

def isCtrlChar(c):
    if len(c)==1 and ord(c) < 32:
        return 1
    else:
        return 0
    
def token_type(token):
    """returns the type of a token: word, punc, annot"""
    ret = []
    token = string.strip(token)
    if token in config.special_tokens.values():
        return ['SPECIAL']
    if token in config.reserved_characters.values():
        return ['PUNC']
    if not isPrintable(str(token)):
        ret.append('UNPRINTABLE')
        return ret
    if len(token) <= 1:
        if isCtrlChar(token):
            ret.append('CONTROL_CHAR')
        if token in config.symbols:
            ret.append('SYMBOL')
        if token in config.lbrackets:
            ret.append('LBRAC')
        if token in config.rbrackets:
            ret.append('RBRAC')
        if token in config.punctuation:
            ret.append('PUNC')
    elif token[0]=='<' and token[-1] == '>':
        if token[1]=='/':
            ret.append('ANNOTATION_E')
        else:
            ret.append('ANNOTATION_S')            
        return ret    
    if allLetters(token):
        ret.append('WORD')
        if len(token) >= config.longword:
            ret.append('LONG')
    if allUpper(token):
        ret.append('ALL_UPPER')
    elif token[0] in string.uppercase:
        ret.append('CAPITALIZED')
    elif allLower(token):
        ret.append('ALL_LOWER')
    if isDigits(token):
        ret.append('NUM')
        ret.append(str(len(token))+'_DIGIT_NUM')
        if len(token)<=2:
            ret.append('S_NUM')
    if len(token)==1:
        ret.append('S_CHAR')
    if lettersDigits(token):
        ret.append('LETTERS_AND_DIGITS')
    return ret

class gazette:
    def __init__(self,tags,gazfilename):
        self._gaz = {}
        gfile = open(gazfilename)
        while 1:
            line = gfile.readline()
            if not line:
                break
            self._gaz[string.lower(string.strip(line))]=tags
        gfile.close()

    def search(self,token):
        if self._gaz.has_key(string.lower(token)):
            return self._gaz[string.lower(token)]
        else:
            return []
    
class Gazetteer:
    def __init__(self, gazdir=os.path.join(config.basedir,'gaz')):
        nerc_tags = {}
        nt = string.split(open(os.path.join(gazdir,'lists.def')).read(),'\n')
        for n in nt:
            file,tags = string.split(n,':')[0],string.split(n,':')[1:]
            if file and tags:
                nerc_tags[file]=tags
        self._gazettes = []
        for g in nerc_tags.keys():
            self._gazettes.append(gazette(nerc_tags[g],os.path.join(gazdir,g)))
        
    def search(self,token):
        ret = []
        for g in self._gazettes:
            sres = g.search(token)
            if sres:
                for sr in sres:
                    if not sr in ret:
                        ret.append(sr)
        return ret
    
    def tag_s(self,s):
        return [self.search(s)]
    
    def tag(self,s):
        ret = []
        t = IEtokeniser(s)
        while 1:
            tok = t.next()
            if not tok:
                break
            ret.append((tok,self.search(tok)))
        return ret
        
    def untag(self, t):
        s = ''
        for x in t:
            s = s + x[0] + ' '
        return string.strip(s)
        
def testGaz():
    g = Gazetteer()
    #g.tag(open(sys.argv[1]).read())
    try:
        for tok in g.tag(open(sys.argv[1]).read()):
            print tok
    except:
        while 1:
            print "???:>",
            name = string.strip(raw_input())
            if not name:
                break
            print g.tag_s(name)

def pennTreebank(str):
	# heuristic algorithm to identify sentence boundaries
    	# returns a string with a sentence on each line

	#convert to Penn Treebank style

	
	s = re.compile(r'([!\?\.]([\'\"])?)').sub(r'\1\n',str)
	#chop
	s = string.strip(s)

    	# attempt to get correct directional quotes
	s = re.compile(r'^\"',re.MULTILINE).sub(r'``',s)
	# close quotes handled at end
	s = re.compile(r'\.\.\.',re.MULTILINE).sub(r' ...',s)
	s = re.compile(r'([,;:@#\\\$%&])',re.MULTILINE).sub(r' \1',s)

	# Assume sentence tokenization has been done first, so split FINAL periods
	# only.
       	s = re.compile(r'([^.])([.])([]\)}>\"\']*)[ \t]*$',re.MULTILINE).sub(r'\1 \2\3 ',s)
	# however, we may as well split ALL question marks and exclamation points,
	# since they shouldn't have the abbrev.-marker ambiguity problem
       	s = re.compile(r'([\?!])',re.MULTILINE).sub(r' \1 ',s)
	# parentheses, brackets, etc.
       	s = re.compile(r'([][\(\){}<>])',re.MULTILINE).sub(r' \1 ',s)
       	s = re.compile(r'--',re.MULTILINE).sub(r' -- ',s)

	# NOTE THAT SPLIT WORDS ARE NOT MARKED.  Obviously this isn't great, since
	# you might someday want to know how the words originally fit together --
	# but it's too late to make a better system now, given the millions of
	# words we've already done "wrong".
	# First off, add a space to the beginning and end of each line, to reduce
	# necessary number of regexps.
       	s = re.compile(r'$',re.MULTILINE).sub(r' ',s)
       	s = re.compile(r'^',re.MULTILINE).sub(r' ',s)
       	s = re.compile(r'"',re.MULTILINE).sub(r' " ',s)

	# possessive or close-single-quote
       	s = re.compile(r'([^\'])\' ',re.MULTILINE).sub('\1 \' ',s)
	# as in it's, I'm, we'd
       	s = re.compile(r'\'([sSmMdD]) ',re.MULTILINE).sub(' \'\\1 ',s)
       	s = re.compile(r'\'ll',re.MULTILINE).sub(' \'ll ',s)
       	s = re.compile(r'\'re',re.MULTILINE).sub(' \'re ',s)
       	s = re.compile(r'\'ve',re.MULTILINE).sub(' \'ve ',s)
       	s = re.compile(r'\'LL',re.MULTILINE).sub(' \'LL ',s)
       	s = re.compile(r'\'RE',re.MULTILINE).sub(' \'RE ',s)
       	s = re.compile(r'\'VE',re.MULTILINE).sub(' \'VE ',s)
       	s = re.compile(r'N\'T',re.MULTILINE).sub(' N\'T ',s)
       	s = re.compile(r'n\'t',re.MULTILINE).sub(' n\'t ',s)

       	s = re.compile(r' ([Cc])annot ',re.MULTILINE).sub(r' \1an not ',s)
       	s = re.compile(r' ([Dd])\'ye ',re.MULTILINE).sub(' \\1\' ye',s)
      	s = re.compile(r' ([Gg])onna ',re.MULTILINE).sub(r' \1on na ',s)
       	s = re.compile(r' ([Gg])imme ',re.MULTILINE).sub(r' \1im me ',s)
      	s = re.compile(r' ([Gg])otta ',re.MULTILINE).sub(r' \1ot to ',s)
     	s = re.compile(r'([Mm])ore\'n',re.MULTILINE).sub(' \\1ore \'n ',s)
       	s = re.compile(r' ([Ll])emme ',re.MULTILINE).sub(r' \1em me ',s)
       	s = re.compile(r' \'([Tt])is',re.MULTILINE).sub(' \'\\1 is ',s)
      	s = re.compile(r' \'([Tt])was ',re.MULTILINE).sub(' \'\\1 was ',s)
       	s = re.compile(r' ([Ww])anna ',re.MULTILINE).sub(r' \1an na ',s)

	# clean out extra spaces
       	s = re.compile(r' +',re.MULTILINE).sub(r' ',s)
       	s = re.compile(r'^ *',re.MULTILINE).sub(r'',s)

	#UGLY HACK for the fact that email addresses and message headers get split at .
        #Brilltag will fail with short sentences
        s2 = ''
        for l in s.split('\n'):
            if len(l) > 20: #hard-coded minimum line len
                s2 = s2 + l + '\n'
            else:
                s2 = s2 + l
	return s2

class BrillTag:
    def __init__(self, path_to_brilltag=config.BRILLTAGPATH):
        #interface to brilltag POS tagger
        self.path = path_to_brilltag
        if not os.path.isfile(self.path):
            errmsg = "Error: cant locate directory "+self.path
            sys.stderr.write(errmsg)
            raise IOError
        self.bt_s_out = ""
        self.bt_s_err = ""
        self.POSTAGS={'CC':0,
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
        
    def tag(self,s,inpenntreebank=1):
        if not inpenntreebank:
            s = pennTreebank(s)
        tmpname = tempfile.mktemp()
        tfile = open(tmpname,'w')
        tfile.write(s)
        tfile.close()
        pwd = os.getcwd()
        os.chdir(os.path.dirname(self.path))
        exestr = self.path+" LEXICON "+tmpname+" BIGRAMS LEXICALRULEFILE CONTEXTUALRULEFILE"
        taggersout,taggersin,taggerserr = popen2.popen3(exestr)
        self.bt_s_out = taggersout.read()
        self.bt_s_err = taggerserr.read()
        os.remove(tmpname)
        os.chdir(pwd)
        return self.bt_s_out
		
    def tagStats(self,str,tagged="",pc=""):
        if not tagged:
            s = self.tag(str)
        else:
            s = str
        for x in string.split(s):
            tag = string.split(x,'/')[-1]
            if self.POSTAGS.has_key(tag):
				self.POSTAGS[tag] = self.POSTAGS[tag] + 1
        if pc:
            total = 0
            for x in self.POSTAGS.keys():
                total = total + self.POSTAGS[x]
            for x in self.POSTAGS.keys():
				self.POSTAGS[x] = self.POSTAGS[x]/float(total)
        return self.POSTAGS

    def wordsWithTag(self,str,tag,tagged=""):
        words = ""
        if not tagged:
            s = self.tag(str)
        else:
            s = str
        for x in string.split(s):
            w,t = string.split(x,'/')
            if t == tag:
                words = words +" "+ w
        return words

class Chunker:
    def __init__(self,datadir=os.path.join(config.basedir,'data'),se=1):
        self.chunks = []
        self.se=se
        
        chunkfile = open(os.path.join(datadir,'NP.chunks'))
        for line in chunkfile:
            line = line.strip()
            if line and line[0]!='#':
                l = len(line.split())
                if not self.se:
                    subline = 'NP '*l
                else:
                    subline = 'NP_s '
                    if l > 1:
                        subline = subline + (l-2)*'NP_i ' + 'NP_e '
                self.chunks.append((line+' ',subline))
        chunkfile.close()

        chunkfile = open(os.path.join(datadir,'VP.chunks'))
        for line in chunkfile:
            line = line.strip()
            if line and line[0]!='#':
                l = len(line.split())
                if not self.se:
                    subline = 'VP '*l
                else:                
                    subline = 'VP_s '
                    if l > 1:
                        subline = subline + (l-2)*'VP_i ' + 'VP_e '
                self.chunks.append((line+' ',subline))
        chunkfile.close()


    def __str__(self):
        s = ''
        for c in self.chunks:
            s = s + str(c) + '\n'
        return s
    
    def chunk(self, s):
        """takes a string of POS symbols and returns a chunk string"""
        s = string.split(string.strip(s))
        #make sure s has a single space between each token
        s = ' '.join(s) + ' '
        for c in self.chunks:
            s = s.replace(c[0],c[1])
        return s
                    
def testChunker():
    c = Chunker()
    print c
    while 1:
        print '>> ',
        txt=raw_input()
        if txt == 'quit': break
        print c.chunk(txt)
            
def testBrillTag():
    try:
        s = open(sys.argv[1]).read()
    except:
        print "usage: ",sys.argv[0]," inputfilename"
        sys.exit()
    b = BrillTag()
    print b.tag(s)


class erc:
    def __init__(self, max_lookahead=7):
        self.max_lookahead = max_lookahead

        
    def tag_res(self, res):
        """takes a list of tokens and looks marks sequences of tokens that look like tokens"""
        self.res = res
        for i in range(len(self.res)):
            self.res[i]['erc'] = []
        for i in range(len(self.res)):
            self._rec_initial(i)
        for i in range(len(self.res)):
            self._rec_person(i)
            self._rec_time(i)
                
        
    def _rec_initial(self,i):
        tok = self.res[i]['token']
        try:
            self.res[i+1]
        except:
            return
        if len(tok)==1 and  tok in string.uppercase and self.res[i+1]['token']=='.':
            self.res[i]['erc'].append('initial')

    def _rec_person(self,i):
        """ a sequence of capitalized tokens that are starts with title or first_name and continues with names, dots, initials, post_names - crude but effective"""
        tok = self.res[i]['token']
        count=0
        if 'person' in self.res[i]['erc']:
            pass
        elif 'title' in self.res[i]['gaz'] or 'person_first' in self.res[i]['gaz'] and i < len(self.res)-1:
            window = self.res[i:i+self.max_lookahead+1]
            count = 1
            while 'person_first' in window[count]['gaz'] or 'person_last' in window[count]['gaz'] or window[count]['token']=='.' or 'initial' in window[count]['erc'] or 'title_post' in window[count]['gaz']:
                if not ('CAPITALIZED' in window[count]['types'] or  window[count]['token']=='.' or 'ALL_UPPER' in window[count]['types']):
                    break
                count = count + 1
                if count == len(window): break                               
                #print count,window[count],self.res[i+count]
            while window[count-1]['token']=='.':
                count = count - 1
        if count >=2:
            for c in range(count):
                if not 'person' in self.res[i+c]['erc']:
                    self.res[i+c]['erc'].append('person')

    def _rec_time(self,i):
        count=0
        if 'NUM' in self.res[i]['types']:
            window = self.res[i:i+self.max_lookahead+1]
            #print window[0]['token'],window[1]['token'],window[2]['token']
            l = len(window)
            count = 0
            if len(window) >=2 and (window[1]['token']=='am' or window[1]['token']=='pm'):
                count = 2
            elif len(window)>=3 and window[1]['token']==':' and 'NUM' in window[2]['types']:
                count = 3
                if len(window)>=4:
                    if window[count]['token'].lower()=='am' or window[count]['token'].lower()=='pm':
                        count = count + 1
        if count >=1:
            for c in range(count):
                if not 'time' in self.res[i+c]['erc']:
                    self.res[i+c]['erc'].append('time')
                    
class IEtagger:
    def __init__(self,tag_special=1,allow_unprintable=0):
        self._postagger = BrillTag()
        self._gaz = Gazetteer()
        self.p = porterstemmer.PorterStemmer()
        self.nl=tag_special
        self.allow_unprintable=allow_unprintable
    def stem_word(self,word):
        stem = self.p.stem(word, 0,len(word)-1)
        suffix = ''
        if len(stem) < len(word):
            suffix = word[-(len(word)-len(stem)):]
        elif len(stem) == len(word) and stem[-1] != word[-1]:
            suffix = word[-1]
        return stem,suffix

    def tag(self,s):
        s = string.strip(s)
        res = []
        s_annots = []
        if self.nl:
            for sp in config.special_tokens.keys():
                s = string.replace(s,sp,' '+config.special_tokens[sp]+' ')
        s = pennTreebank(s)
        s = string.replace(s,'< ','<')
        s = string.replace(s,' </','</')
        s = string.replace(s,' >','>')
        gaz_res = self._gaz.tag(s)
        #del self._postagger.POSTAGS['CD']
        #del self._postagger.POSTAGS['SYM']
        pos_res=[]
        patt = r'<.*?>'
        s = re.sub(patt,' ',s)
        
        if self.nl:
            for sp in config.special_tokens.keys():
                s = string.replace(s,' '+config.special_tokens[sp]+' ',sp)
        
        #print "XXXPRETAG",s
        s = self._postagger.tag(s)
        #print "XXXTAG",s
        toks = string.split(s)
        for t in toks:
            word,tag = '',''
            for wrd in string.split(t,'/')[:-1]:
                word = word + wrd+'/'
            word = word[:-1]
            tag = string.split(t,'/')[-1]
            if isword(word) and self._postagger.POSTAGS.has_key(tag):
                pos_res.append((word,tag))
        p_i = 0
        #print pos_res, "\n\n",gaz_res,"\n"
        for g_i in range(len(gaz_res)):
            t_res={'token':'','pos':'','stem':'','suffix':'','gaz':[],'types':[],'annotations':[]}
            t_res['token']=string.lower(gaz_res[g_i][0])
            t_res['gaz']=gaz_res[g_i][1]
            t_res['types']=token_type(gaz_res[g_i][0])
            #print "XXX",gaz_res[g_i][0],pos_res[p_i][0]
            if gaz_res[g_i][0] == pos_res[p_i][0]:
                if not gaz_res[g_i][0] in config.special_tokens.values():
                    t_res['pos'] = pos_res[p_i][1]
                if p_i < (len(pos_res)-1):
                    p_i = p_i + 1
            t_res['stem'],t_res['suffix'] = list(self.stem_word(t_res['token']))

            ### must deal with a word having two or more annotations!

            if 'ANNOTATION_E' in t_res['types']:
                res[-1]['annotations'].append(t_res['token'])
            else:
                if 'ANNOTATION_S' in t_res['types']:
                    s_annots.append(t_res['token'])
                else:
                    res.append(t_res)
                    if s_annots:
                        res[-1]['annotations'] = s_annots
                        s_annots = []
        if p_i != len(pos_res)-1:
            print >>sys.stderr,"Failed to match tags!!!",p_i, len(pos_res)-1
            for x in range(p_i,len(pos_res)-1):
                print pos_res[p_i]
            raise TaggingError
        if not self.allow_unprintable:
            for i in range(len(res)):
                if 'UNPRINTABLE' in res[i]['types'] or 'CONTROL_CHAR' in res[i]['types']:
                    print "Deleting token",res[i]
                    res[i] = 'DELETEME'
            while 'DELETEME' in res:
                res.remove('DELETEME')
        #res has been tagged:this would be a good time to do chunking
        p_str = ''
        for r in res:
            if r['pos']:
                p_str = p_str + r['pos'] + ' '
            else:
                p_str = p_str + 'X '
        c = Chunker()
        c_str = c.chunk(p_str.strip())
        chunks = c_str.strip().split()
        if not len(chunks)==len(res):
            raise "Chunking failure!"
        for i in range(len(chunks)):
            res[i]['chunks'] = []
            if chunks[i] != 'X' and not self._postagger.POSTAGS.has_key(chunks[i]):
                res[i]['chunks'].append(chunks[i])
        #check for entities
        n = erc()
        n.tag_res(res)
        return res

class BIOtagger:
    def __init__(self,tag_special=1,allow_unprintable=0):
        self._gaz = Gazetteer()

    def tag(self,s):
        s = string.strip(s)
        res = []
        s_annots = []
        gaz_res = self._gaz.tag(s)

        for g_i in range(len(gaz_res)):
            t_res={'token':'','pos':'','stem':'','suffix':'','gaz':[],'types':[],'annotations':[],'chunks':[],'erc':[]}
            t_res['token']=string.lower(gaz_res[g_i][0])
            t_res['gaz']=gaz_res[g_i][1]
            t_res['types']=token_type(gaz_res[g_i][0])
            if 'ANNOTATION_E' in t_res['types']:
                res[-1]['annotations'].append(t_res['token'])
            else:
                if 'ANNOTATION_S' in t_res['types']:
                    s_annots.append(t_res['token'])
                else:
                    res.append(t_res)
                    if s_annots:
                        res[-1]['annotations'] = s_annots
                        s_annots = []

        return res
    
def testIEtagger():
    g = IEtagger()
    s = open(sys.argv[1]).read()
    res = g.tag(s)
    format = "%-20s %-10s %-10s %-20s %-30s %-30s"
    print format %('Token','POS', 'CHUNK','ERC','GAZ','TYPES')
    for r in res:
        print format % (r['token'],r['pos'],r['chunks'],r['erc'],r['gaz'],r['types'])
  
if __name__=='__main__':
    try:
        sys.argv[1]
    except:
        usage()
        sys.exit()
    #test(open(sys.argv[1]).read())
    #test_nameGaz()
    #testGaz()
    testIEtagger()
    #testChunker()
    #testIEtokeniser(open(sys.argv[1]).read())
