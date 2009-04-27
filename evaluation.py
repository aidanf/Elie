#!/usr/bin/python

import multiLevelExtractor ,utils
import getopt,sys,random,os,sys
from math import ceil
import profile,pstats
from utils import log
import config
import string

if config.use_psyco:
    try:
        import psyco
        psyco.full()
    except:
        print >>sys.stderr,"Warning: cannot import psycho -> execution will be slower!"
sys.setcheckinterval(1000)

class ResultSet:
    def __init__(self):
        """each result is a tuple of the form (filename, extracted, actual ,predicted_se, actual_se)"""
        self.results = []
        
    def __str__(self):
        s = ''
        for r in self.results:
            s = s + str(r) + "\n"
        return s
        
    def append(self, r):
        self.results.append(r)

    def write_bwi_scorer(self, outfilestem,iteration=0):
        scores = {}
        s_act = {}
        s_pred = {}
        for res in self.results:
            for k in res[2].keys():
                if not s_act.has_key(k):
                    s_act[k] = "actual\n"
                if not s_pred.has_key(k):
                    s_pred[k] = ""
                if not scores.has_key(k):
                    scores[k] = "iteration " + str(iteration) + "\n"
                s_act[k] = s_act[k] + "file "+res[0] + " "
                s_pred[k] = s_pred[k] + "file " +res[0] + " "
                for it in res[2][k]:
                    s_act[k] = s_act[k] + str(it[0]) + " " + str(it[1]) + " "
                for it in res[1][k]:
                    s_pred[k] = s_pred[k] + str(it[0]) + " " + str(it[1]) + " " + str(it[2][0]*it[2][1]*it[2][2]) + " "
                s_act[k] = s_act[k] + "\n"
                s_pred[k] = s_pred[k] + "\n"
        for k in scores.keys():
            scores[k] = scores[k]+s_act[k]+"endactual\ncallback bwi\n"+s_pred[k]
            outfile= open(outfilestem+'.'+str(iteration)+'.'+str(k)+'.bwi','w')
            outfile.write(scores[k])
            outfile.close()
                    
    def write_MUC_scorer(self, outstream):
        pass


class Experiment:
    def __init__(self,train,test,datadir,field,number=0,name=config.name):
        self.train = train
        self.test = test
        self.datadir = datadir
        #self.results = ResultSet()
        self.number = number
        self.name = name
        self.field = field
        
    def run(self,verbose=2):
        log(2,"Trial number "+str(self.number)+"\n")
        e = multiLevelExtractor.TwoLevelExtractor(self.datadir,self.field, name=self.name)
        e.learn(self.train)
        n_files = len(self.test)
        count = 0
        e.extract(self.test)
        e.log_extractions(n=self.number)
        e.print_extractions()
        #e.print_extractions(ex,act,se_pred)
        """
        for tf in self.test:
            self.results.append((tf,ex[tf],act[tf],se_pred[tf],se_act[tf]))
        self.results.write_scores(self.datadir, self.number)
        """
        del(e)

class randomSplitExperiment:
    def __init__(self,corpus,datadir,field,ntrials=10,train_proportion=0.5):
        self.datadir = datadir
        self.field=field
        self.corpus = corpus
        self.experiments = []
        desc_file = open(os.path.join(self.datadir,"parameters.txt"),'w')
        config.describe("%s trials of %s split"%(ntrials,train_proportion),outstream=desc_file)
        desc_file.close()
        for n in range(ntrials):
            random.shuffle(self.corpus)
            random.shuffle(self.corpus)
            split_point = int(ceil(len(self.corpus)*train_proportion))
            train = self.corpus[:split_point]
            test = self.corpus[split_point:]
            split_file = open(os.path.join(datadir,'elie.'+field+'.'+str(n)+'.split'),'w')
            for t in train:
                t = os.path.split(t)[-1]
                print >>split_file,t
            print >>split_file, 20*'*'
            for t in test:
                t = os.path.split(t)[-1]
                print >>split_file,t
                
            new_exper = Experiment(train,test,self.datadir,self.field,number=n)
            self.experiments.append(new_exper)

        
    def run(self):
        for exp in self.experiments:
            exp.run()
            #exp.results.write_bwi_scorer(os.path.join(exp.datadir,'bwiscore'),exp.number)

class definedSplitExperiment:
    def __init__(self,corpusdir, datadir, field, splitfiles):
        self.datadir = datadir
        self.field=field
        self.corpusdir = corpusdir
        self.splitfiles = splitfiles
        self.experiments = []
        desc_file = open(os.path.join(self.datadir,"parameters.txt"),'w')
        desc_str = "Using pre-defined splits:\n"
        for sf in self.splitfiles:
            desc_str = desc_str + sf + "\n"
        config.describe(desc_str,outstream=desc_file)
        desc_file.close()
        for sf in self.splitfiles:
            n = os.path.split(sf)[-1].split('.')[2]
            f = open(sf)
            tmp1,tmp2 = string.split(f.read(),20*'*')
            train = []
            test = []
            for tmp in tmp1.split('\n'):
                tmp = tmp.strip()
                if tmp:
                    tmp = os.path.join(self.corpusdir,tmp)
                    if tmp[-9:] != '.elie.pre':
                        tmp = tmp + '.elie.pre'
                    train.append(tmp)
            for tmp in tmp2.split('\n'):
                tmp = tmp.strip()
                if tmp:
                    tmp = os.path.join(self.corpusdir,tmp)
                    if tmp[-9:] != '.elie.pre':
                        tmp = tmp + '.elie.pre'
                    test.append(tmp)
                
            #print "XXX",train,"\n\n",test
            #raw_input()
            split_log = open(os.path.join(datadir,'elie.'+field+'.'+str(n)+'.split'),'w')
            for t in train:
                t = os.path.split(t)[-1]
                print >>split_log,t
            print >>split_log, 20*'*'
            for t in test:
                t = os.path.split(t)[-1]
                print >>split_log,t
                
            new_exper = Experiment(train,test,self.datadir,self.field,number=n)
            self.experiments.append(new_exper)

        
    def run(self):
        for exp in self.experiments:
            exp.run()
            #exp.results.write_bwi_scorer(os.path.join(exp.datadir,'bwiscore'),exp.number)
            

def usage():
    print >>sys.stderr,"""
    %s -f field -t trainCorpusDirectory -D dataDirectory [-T testCorpusDirectory] [-s splitfilebase] [-mpnvh]

       If -t and -T are are set, then we train on trainCorpusDirectory and test on testCorpusDirectory
       Otherwise we do repeated random splits on trainCorpusDirectory
       Options:
          -m use cached models (NYI)
          -p set train proportion default=0.5
          -n number of trials default=10
          -v version info
          -h help""" % sys.argv[0]

if __name__=='__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:t:T:D:n:p:s:mvh')
    except getopt.error, msg:
        print msg
        usage()
        sys.exit(2)
    options = {'t_prop' : 0.5, 'ntrials' : 10}
    for opt, arg in opts:
        if opt == '-v':
            sys.stderr.write("This is %s version %s.\n" % (config.name, config.version))
            sys.exit(0)
        if opt == '-h':
            usage()
            sys.exit(0)
        if opt == '-f':
            options['FIELD'] = arg
        if opt == '-t':
            options['TRAINDIR'] = arg
        if opt == '-s':
            options['SPLITBASE'] = arg
        if opt == '-T':
            options['TESTDIR'] = arg
        if opt == '-D':
            options['DATADIR'] = arg
        if opt == '-n':
            options['ntrials'] = int(arg)
        if opt == '-p':
            options['t_prop'] = float(arg)
    if not options.has_key('FIELD') or not options.has_key('TRAINDIR') or not options.has_key('DATADIR'):
        usage()
        sys.exit(2)
 


    #test_corpus = utils.fileList(sys.argv[3],list_suffix=1,list_non_suffix=0)
    #exper = Experiment(sys.argv[2],test_corpus, sys.argv[1])
    # need to pass fields to experiment
    if options.has_key('SPLITBASE'):
        import glob
        splitfiles = glob.glob(options['SPLITBASE']+'*.split')
        print >>sys.stderr,"Experiment using the following pre-defined train/test splits:"
        for sf in splitfiles:
            print >>sys.stderr,"\t",sf
        exper = definedSplitExperiment(options['TRAINDIR'],options['DATADIR'],options['FIELD'], splitfiles)
    elif not options.has_key('TESTDIR'):        
        corpus = utils.fileList(options['TRAINDIR'],list_suffix=1,list_non_suffix=0)
        exper = randomSplitExperiment(corpus,options['DATADIR'],options['FIELD'],ntrials=options['ntrials'],train_proportion=options['t_prop'])
    else:
        train = utils.fileList(options['TRAINDIR'],list_suffix=1,list_non_suffix=0)
        test = utils.fileList(options['TESTDIR'],list_suffix=1,list_non_suffix=0)
        exper = Experiment(train,test,options['DATADIR'],options['FIELD'])
    exper.run()
    #exper.results.write_bwi_scorer(os.path.join(exper.datadir,'bwiscore'))
