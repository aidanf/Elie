#!/usr/bin/python

import glob,sys,config,tempfile,string, types, os,copy
import utils, tagmatch
from utils import log
from UserDict import UserDict

def start_tag(field):
    return '<'+field+'>'

def end_tag(field):
    return '</'+field+'>'

class Instance(UserDict):
    def attributeArray(self,att_list):        
        """returns an array of attributes and values that can be used to create a weka instance"""
        d_array = []
        for att in att_list:
            if self.has_key(att):
                d_array.append(1.0)
            else:
                d_array.append(0.0)
        if self['ANNOTATION']:
            d_array.append(1.0)
        else:
            d_array.append(0.0)
        return d_array

    def center(self):
        ret = {'token':'','pos':'','gaz':[],'types':[]}
        for k in self.keys():
            tmp = string.split(k,'_')
            tp,pos = tmp[0],tmp[-1]
            val = ''
            for v in tmp[1:-1]:
                val = val + v
            if pos == '0':
                if tp == 'TOKEN':
                    ret['token'] = val
                if tp == 'POS':
                    ret['pos'] = val
                if tp == 'POS':
                    ret['pos'] = val
                if tp == 'G':
                    ret['gaz'].append(val)
                if tp == 'T':
                    ret['types'].append(val)
        return ret
                
    

class Instances:
    def __init__(self, name='test'):
        self._instances=[] #all the instances
        self._start_index = [] #an index to the positions of the positives
        self._end_index = []
        self._doc_index = []
        self.name=name
        self.__state=0
        
    def __len__(self):
        return len(self._instances)

    def __str__(self):
        attributes = {}
        for i in self._instances:
            for k in i.keys():
                if not attributes.has_key(k):
                    attributes[k] = 1
        n_attributes = len(attributes.keys())
        n_instances = len(self._instances)
        n_start = len(self._start_index)
        n_end = len(self._end_index)
        description = """
        %s attributes
        %s instances :: %s starts : %s ends\n\n""" % (n_attributes,n_instances, n_start,n_end)
        return description

    
    def printArff(self,out_stream=sys.stdout,dataset=[]):
        features = {'ANNOTATION':-1}
        if not dataset:
            feature_list = []
            index = 0
            for inst in self._instances:
                feats = inst.keys()
                feats.sort()
                for f in feats:
                    try:
                        features[f]
                    except KeyError:
                        features[f] = index
                        feature_list.append(f)
                        index = index + 1
            features['ANNOTATION'] = index
            #feature_list.sort()
        else:
            for i in range(len(dataset)):
                features[dataset[i]] = i
            feature_list = dataset
            features['ANNOTATION'] = len(dataset)
            #print features,feature_list
        out_stream.write("@relation "+self.name+"\n")
        for f in feature_list:
            out_stream.write("@attribute " + f + " {0, 1}\n")
        out_stream.write("@attribute ANNOTATION {0, 1}\n")
        out_stream.write("@data\n")
        for inst in self._instances:
            tmp = []
            #we dont have to iterate over all the features!
            for feat in inst.keys():
                try:
                    tmp.append((features[feat],inst[feat]))
                except KeyError:
                    pass
            tmp.sort()
            s = '{'
            for t in tmp[:-1]:
                s = s +str(t[0]) + ' ' + str(t[1])+ ', '
            if inst['ANNOTATION']:
                s = s + str(features['ANNOTATION']) + ' 1}\n'
            else:
                if s == '{':
                    s = s + '}\n'
                    print "XXX - no attribute instance",inst
                else:
                    s = s[:-2] + '}\n'
            out_stream.write(s)
        out_stream.flush()

    def add(self, other):
        if isinstance(other, Instances):
            l = len(self._instances)
            self._doc_index.append(l)
            self._instances = self._instances + other._instances
            self._start_index = self._start_index + [ x + l for x in other._start_index]
            self._end_index = self._end_index + [ x + l for x in other._end_index]
        elif isinstance(other, Instance):
            #raise "How to deal with single instance?"
            #cannot add instances singularly to another set of instances - they must only
            #be added temperorily to a set of instances that will be added to the set of instances later
            self._instances.append(other)
        else:
            raise "Can't add that type" + type(other)

            """
            self._instances.append(other)
            if other['ANNOTATION']:
                if 
                self._pos_index.append(len(self._instances)-1)"""

    def set_to_start(self):
        if self.state() =='end':
            for x in self._end_index:
                self._instances[x]['ANNOTATION']=0
        for x in self._start_index:
            self._instances[x]['ANNOTATION']=1            
        self.__state='start'

    def set_to_end(self):
        if self.state() =='start':
            for x in self._start_index:
                self._instances[x]['ANNOTATION']=0
        for x in self._end_index:
            self._instances[x]['ANNOTATION']=1            
        self.__state='end'

    def state(self):
        return self.__state

    def get_tokens(self, i, j):
        ret = []
        for x in self._instances[i:j+1]:
            ret.append(x.center()['token'])
        return ret

    def get_actual(self):
        """returns a list of start-end pairs"""
        ret = []
        if len(self._start_index) == len(self._end_index):
            for i in range(len(self._start_index)):
                ret.append((self._start_index[i],self._end_index[i],1))
        else:
            raise "Data Error: Dataset doesn't have the same number of start and end tags"
        return ret

    def get_actual_starts(self):
        return self._start_index

    def get_actual_ends(self):
        return self._end_index


class Document(Instances):
    """
    Build a set of instances from a preprocessed document
    d : a list of preprocessed token dictionaries
    x    filters : a list of filter objects to be applied to instances to determine whether we add them
    """
    def __init__(self,d,field,window=3,token=1,stem=1,suffix=1,pos=1,types=1,gaz=1,chunk=1,erc=1):
        Instances.__init__(self)
        self.field=field
        for i in range(len(d)):
            inst = Instance()
            for j in range(-window,window+1):
                if i+j >= 0 and i+j < len(d):
                    if token:                        
                        if d[i+j]['token'] in config.reserved_characters.keys():
                            d[i+j]['token'] = str(config.reserved_characters[d[i+j]['token']])
                        if len(d[i+j]['token']) < 1:
                            d[i+j]['token'] = 'INVISIBLE'
                        inst['TOKEN_'+d[i+j]['token']+'_'+str(j)] = 1
                    if pos:
                        if d[i+j]['pos']:
                            inst['POS_'+d[i+j]['pos']+'_'+str(j)] = 1                    
                    
                    if stem:
                        if d[i+j]['stem'] in config.reserved_characters.keys():
                            d[i+j]['stem'] = str(config.reserved_characters[d[i+j]['stem']])
                        if len(d[i+j]['stem']) < 1:
                            d[i+j]['stem'] = 'INVISIBLE'
                        inst['STEM_'+d[i+j]['stem']+'_'+str(j)] = 1
                    if suffix:
                        if d[i+j]['suffix']:
                            inst['SUFFIX_'+d[i+j]['suffix']+'_'+str(j)] = 1                    
                    if types:
                        for t in d[i+j]['types']:
                            inst['T_'+t+'_'+str(j)] = 1
                    if gaz:
                        for t in d[i+j]['gaz']:
                            inst['G_'+t+'_'+str(j)] = 1
                    if chunk:
                        for t in d[i+j]['chunks']:
                            inst['C_'+t+'_'+str(j)] = 1
                    if erc:
                        for t in d[i+j]['erc']:
                            inst['E_'+t+'_'+str(j)] = 1
                    if j == 0:
                        for t in d[i]['annotations']:
                            if t == start_tag(field):
                                self._start_index.append(i)
                            if t == end_tag(field):
                                self._end_index.append(i)
                    inst['ANNOTATION']=0
            self.add(inst)

class Dataset(Document):
    def __init__(self, corpus, field):
        doc_index = []
        self._corpus_files = []
        if type(corpus) is types.ListType:
            corpus_files = corpus
        elif os.path.isfile(corpus):      
            corpus_files = [corpus]
        else:
            #corpus is a directory
            corpus_files = utils.fileList(corpus,list_suffix=1,list_non_suffix=0)

        doc = []
        for f in corpus_files:
            l = len(doc)
            doc_index.append(l)
            log(2,'. ')
            log(4,' '+f+'\n')
            d = open(f)
            while 1:
                tok = d.readline()
                if not tok:
                    break
                doc.append(eval(tok,globals()))
            d.close()
        ###need to record the breaks between documents!
        # creating a single Document saves speed, but will result in some dubious
        # features e..g. x_1 in the last instance of one document where x is first
        # in next doc. these should be irrelevant and filtered though
        Document.__init__(self, doc, field,window=config.window,stem=config.stem,suffix=config.suffix,token=config.token,pos=config.pos,types=config.types,gaz=config.gaz,chunk=config.chunk,erc=config.erc)
        self._corpus_files = corpus_files
        self._doc_index = doc_index

    def get_corpus_files(self):
        return self.corpus_files
    
    def write_instances(self, data_dir, name):
        ret = {}
        for k in ['start', 'end']:
            f_name = os.path.join(data_dir,name+'.'+self.field+'.'+k+'.arff')
            outfile= open(f_name,'w')
            ret[k] = f_name
            apply(eval('self.set_to_'+k))
            if k != self.state():
                raise ("Dataset error: failed to change state")
            self.printArff(out_stream=outfile)
            outfile.close()
        return ret

    def map_instance_to_file(self,index):
        """takes an index of an instance and associates it with the file it came from"""
        for i in range(len(self._doc_index)):            
            if i == len(self._doc_index)-1:
                if index >= self._doc_index[i]:
                    return self._corpus_files[i]
                else:
                    return ''
            elif index >= self._doc_index[i] and index < self._doc_index[i+1]:
                return self._corpus_files[i]
        return ''

    def get_corpus_files(self):
        return self._corpus_files

def write_reduced_instances(dataset, data_dir, name, lookahead):
    ret = {}

    f_name = os.path.join(data_dir,name+'.'+dataset.field+'.start.arff')
    outfile= open(f_name,'w')
    ret['start'] = f_name
    dataset.set_to_start()
    tmp = Instances()
    for e in dataset._end_index:
        if e < lookahead: l=e
        else: l=lookahead
        for inst in dataset._instances[e-l:e+1]:
            tmp.add(inst)
    Instances.printArff(tmp,out_stream=outfile)
    outfile.close()
        
    f_name = os.path.join(data_dir,name+'.'+dataset.field+'.end.arff')
    outfile= open(f_name,'w')
    ret['end'] = f_name
    dataset.set_to_end()
    tmp = Instances()
    for s in dataset._start_index:
         for inst in dataset._instances[s:s+lookahead+1]:
            tmp.add(inst)
    Instances.printArff(tmp,out_stream=outfile)
    outfile.close()

    return ret
        
if __name__=='__main__':
    d = Dataset(sys.argv[1], 'speaker')
    d.printArff()
