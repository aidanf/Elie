#! /usr/bin/python
 
import sys,types,os,tempfile,string,popen2
import utils, tagmatch
from instances import *
from utils import log


class Prediction:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __str__(self):
        return "%s" % str(self.n)
    def __repr__(self):
        return str(self.__dict__)        
    def __sub__(self, other):
        return self.n - other.n
    def __lt__(self, other):
        return self.n < other.n
    def __gt__(self, other):
        return self.n > other.n
    def __le__(self, other):
        return self.n <= other.n
    def __ge__(self, other):
        return self.n >= other.n
    def set(self, **kwds):
        self.__dict__.update(kwds)
    def __cmp__(self,other):
        if self.n == other.n:
            return 0
        elif self.n > other.n:
            return 1
        elif self.n < other.n:
            return -1
    def __hash__(self):
        return self.n

    def confidence(self):
        return self.confidence[1] * self.confidence[2]

class predictionSetIterator:
    def __init__(self, ps):
        self.count=0
        self.ps = ps
    def __iter__(self):
        return self
    def next(self):    
        if self.count >= len(self.ps):
            raise StopIteration
        nxt = self.ps.get_prediction(self.count)
        self.count = self.count + 1
        return nxt
    
class PredictionSet:
    def __init__(self):
        self.__predictions = []
    def __len__(self):
        return len(self.__predictions)

    def __iter__(self):
        return predictionSetIterator(self)
    
    def add(self, p):
        self.__predictions.append(p)

    def get_indices(self):
        ret = []
        for p in self.__predictions:
            ret.append(p.n)
        return ret
    
    def get_prediction(self,i):
        return self.__predictions[i]

class ExtractionSet:
    def __init__(self, starts=[], ends=[], extracts=[]):
        self.__extracts = extracts
        self.__predictions_start = starts
        self.__predictions_end = ends

    def __str__(self):
        return str(self.__extracts)

    def get_extracts(self):
        return self.__extracts

    def get_predictions_start(self):
        return self.__predictions_start
    
    def get_predictions_end(self):
        return self.__predictions_end

    def set_extracts(self, e):
        self.__extracts = e
    def set_predictions_start(self, s):
        self.__predictions_start = s
    def set_predictions_end(self, e):
        self.__predictions_end = e

class Extractor:
    #class for each level extractor
    def __init__(self,data_dir,field,name=config.name):
        self.data_dir=data_dir
        self.name = name
        self.field=field
        self._arff = {}
        self._models = {}
        self._model_files = {}


    def learn(self, corpus='', dataset=''):
        if corpus:
            self.__train_dataset = Dataset(corpus, self.field)
        elif dataset:
            self.__train_dataset = dataset
        else:
            raise "Cannot learn without corpus or dataset"
        print "Training Corpus:", self.__train_dataset
        self.tagMatcher = tagmatch.histogramTagMatcher(self.__train_dataset.get_actual())
        self._arff = self.__train_dataset.write_instances(self.data_dir, self.name)
        #self.reset_data()
        for k in ['start', 'end']:
            self._models[k] = m = Model(self.data_dir, self.name, learner=config.learner)
            m.filter(self._arff[k])
            m.learn(self._arff[k])
            
    def predict(self, corpus='', dataset=''):
        """returns a dictionary with keys start and end, each being a PredictionSet object"""
        preds = ExtractionSet()
        if corpus:
            self.__test_dataset = Dataset(corpus, self.field)
        elif dataset:
            self.__test_dataset = dataset
        else:
            raise "Cannot learn without corpus or dataset"
        print "Test Corpus:", self.__test_dataset        
        for k in ['start', 'end']:
            t_dataset = []
            train_file = open(self._arff[k])
            while 1:
                line = train_file.readline()
                if line[:5] == '@data':
                    del(t_dataset[-1]) #del 'ANNOTATION'
                    break
                if line[:10] == '@attribute':
                    t_dataset.append(string.split(line)[1])
            train_file.close()
            m = self._models[k]
            arff_name = tempfile.mktemp()
            outfile = open(arff_name,'w')
            apply(eval('self.get_test_dataset().set_to_'+k))
            self.__test_dataset.printArff(out_stream=outfile,dataset=t_dataset)
            outfile.close()
            apply(eval('preds.set_predictions_'+k), [m.predict(arff_name, sparse=1)])
            os.remove(arff_name)
        return preds

    def extract(self, predictions):
        extractions = self.tagMatcher.predict_end(predictions['start'], predictions['end'])
        return extractions

    
    def log_extractions(self, n=0):
        pass

    def print_extractions(self, extractions):
        for e in extractions:
            print "\t",e[2],self.__train_dataset.get_tokens(e[0],e[1])

    def get_train_dataset(self):
        return self.__train_dataset

    def get_test_dataset(self):
        try:
            return self.__test_dataset
        except:
            raise "No test set defined"
        
class ReducedViewExtractor(Extractor):
    def learn(self, corpus='', dataset='', lookahead=10):
        if corpus:
            self.__train_dataset = Dataset(corpus, self.field)
        elif dataset:
            self.__train_dataset = dataset
        else:
            raise "Cannot learn without corpus or dataset"
        print "Training Corpus:", self.__train_dataset
        self.tagMatcher = tagmatch.histogramTagMatcher(self.__train_dataset.get_actual())
        if config.m_window:
            m_window = config.m_window
        else:
            m_window = self.tagMatcher.max_length()
        print "m_window :", m_window
        self._arff = write_reduced_instances(self.__train_dataset,self.data_dir, self.name, m_window)
        #self.reset_data()
        for k in ['start', 'end']:
            self._models[k] = m = Model(self.data_dir, self.name, learner=config.learner)
            m.learn(self._arff[k])


class Model:
    def __init__(self, data_dir, name='', learner='SMO'):
        self.name = name
        self.data_dir = data_dir
        self.learner=learner
        self.learners = { 'SMO':('weka.classifiers.functions.SMO',''),
                          'j48':('weka.classifiers.trees.J48',''),
                          'bayes':('weka.classifiers.bayes.NaiveBayes',''),
                          'winnow':('weka.classifiers.functions.Winnow',''),
                          'neural':('weka.classifiers.functions.MultilayerPerceptron',''),
                          'knn':('weka.classifiers.lazy.IBk',''),
                          'kstar':('weka.classifiers.lazy.KStar',''),
                          'hyper':('weka.classifiers.misc.HyperPipes',''),
                          'jrip':('weka.classifiers.rules.JRip',''),
                          'LMT':('weka.classifiers.trees.LMT',''),
                          'm5':('weka.classifiers.trees.M5P',''),
                          'PART':('weka.classifiers.rules.PART',''),
                          'prism':('weka.classifiers.rules.Prism',''),
                          'OneR':('weka.classifiers.rules.OneR',''),
                          'ridor':('weka.classifiers.rules.Ridor',''),
                          'm5rules':('weka.classifiers.rules.M5Rules',''),
                          'FSD':('weka.classifiers.ucd.ensemble.FeatureSpaceDivider',''),
                          'boost':('weka.classifiers.meta.AdaBoostM1',' -P 20 -S 1 -I 10 -W weka.classifiers.functions.SMO -- -C 1.0 -E 1.0 -G 0.01 -A 1000003 -T 0.0010 -P 1.0E-12 -N 0 -V -1 -W 1')
             }

    def learn(self, arff_file):
        self._arff_file=arff_file
        self._model_file = self._arff_file[:-4] + 'model'
        exe_str = config.java + ' ' + self.learners[self.learner][0] + ' ' + self.learners[self.learner][1] + ' -o -v -t ' + self._arff_file + ' -d ' + self._model_file + ' -T ' + self._arff_file
        print exe_str
        
        s_out,s_err = popen2.popen2(exe_str)
        w_out = s_out.read()
        if not w_out:
            raise "Weka execution error: nothing returned"
        return self._model_file
        
    def predict(self, arff_file, sparse=0):
        print "predicting for",arff_file
        p_ret = PredictionSet()
        exe_str = config.java + ' ' + self.learners[self.learner][0] + ' -o -p 0 -l ' + self._model_file + ' -T ' + arff_file
        s_out,s_err = popen2.popen2(exe_str)
        w_out = string.strip(s_out.read())
        if not w_out:
            raise "Weka execution error: nothing returned"
        predictions = string.split(w_out,'\n')
        for inst in predictions:
            n,prediction,confidence,actual = string.split(inst.strip())
            n,prediction,confidence,actual =  int(n),int(prediction),float(confidence),int(actual)
            if not sparse:
                p_ret.add(Prediction(prediction=prediction, confidence=confidence, actual=actual, n=n))
            else:
                if prediction:
                    p_ret.add(Prediction(prediction=prediction, confidence=confidence, actual=actual, n=n))
        return p_ret
    
    def filter(self, arff_file):
        self._arff_file=arff_file
        #Undersample negative instances
        if config.undersample:
            #first randomize the instances...
            exe_str = config.java + ' weka.filters.unsupervised.instance.Randomize -i %s -o %s.out -c last' % (self._arff_file, self._arff_file)
            print exe_str
            s_out,s_err = popen2.popen2(exe_str)
            if s_out.read():
                os.remove(self._arff_file+'.out')
            else:
                os.rename(self._arff_file+'.out',self._arff_file)
                
            #...then undersample
            exe_str = config.java + ' weka.filters.unsupervised.instance.RemoveNegativePercentage -i %s -o %s.out -c last -P %s' % (self._arff_file, self._arff_file, config.undersample)
            print exe_str
            s_out,s_err = popen2.popen2(exe_str)
            if s_out.read():
                os.remove(self._arff_file+'.out')
            else:
                os.rename(self._arff_file+'.out',self._arff_file)
        #Filter attributes by Information Gain
        if config.filter_n_attributes or config.filter_threshold:
            exe_str = config.java + ' weka.filters.supervised.attribute.AttributeSelection -i %s -o %s.out -c last  -E "weka.attributeSelection.InfoGainAttributeEval" -S "weka.attributeSelection.Ranker' % (self._arff_file, self._arff_file)
            if config.filter_n_attributes:
                print exe_str
                exe_str = exe_str + ' -N ' + str(config.filter_n_attributes) + '"'                
            elif config.filter_threshold:
                print exe_str
                exe_str = exe_str + ' -T ' + str(config.filter_threshold) + '"'
                
            s_out,s_err = popen2.popen2(exe_str)
            if s_out.read():
                os.remove(self._arff_file+'.out')
            else:
                os.rename(self._arff_file+'.out',self._arff_file)
    

class TwoLevelExtractor(Extractor):
    def __init__(self,data_dir,field,name=config.name):
        Extractor.__init__(self,data_dir,field,name)
        self._levels = []
        self._levels.append(Extractor(data_dir,field,name+'.L1'))
        self._levels.append(ReducedViewExtractor(data_dir,field,name+'.L2'))

    def learn(self, corpus):
        self._levels[0].learn(corpus=corpus)
        self.tagMatcher = tagmatch.twoLevelHistogramTagMatcher(self._levels[0].tagMatcher)
        self._levels[1].learn(dataset=self._levels[0].get_train_dataset())

    def extract(self, corpus):
        self.__test_dataset = Dataset(corpus,self.field)
        self._extracts = [self._levels[0].predict(dataset=self.__test_dataset)]
        self._extracts[0].set_extracts(self._levels[0].tagMatcher.predict_end(self._extracts[0].get_predictions_start(),self._extracts[0].get_predictions_end()))        
        self._extracts.append(self._levels[1].predict(dataset=self.__test_dataset))
        ############ tagmatcher should probably take two ExtractionSets as objects and just fill in the extractions
        self._extracts[1].set_extracts(self.tagMatcher.predict_end(self._extracts[0], self._extracts[1]))

        return self._extracts[1]
    
    def log_extractions(self, n=0):
        #L1
        outfile = open(os.path.join(self.data_dir,self.name+'.'+self.field+'.'+str(n)+'.elie.L1.log'),'w')
        starts = []
        for p in self._extracts[0].get_predictions_start(): starts.append(p.n)
        ends = []
        for p in self._extracts[0].get_predictions_end(): ends.append(p.n)        
        outfile.write(str(starts)+"\n")
        outfile.write(str(ends)+"\n")
        outfile.write(str(self._extracts[0].get_extracts())+"\n")
        outfile.write(str(self._levels[0].get_test_dataset().get_actual_starts())+"\n")
        outfile.write(str(self._levels[0].get_test_dataset().get_actual_ends())+"\n")
        outfile.write(str(self._levels[0].get_test_dataset().get_actual())+"\n")
        outfile.close()
        #L2 ##### need to seperate L1 and L2 extractions??? or have generic log_extractions called twice
        outfile = open(os.path.join(self.data_dir,self.name+'.'+self.field+'.'+str(n)+'.elie.L2.log'),'w')
        starts = []
        for p in self._extracts[1].get_predictions_start(): starts.append(p.n)
        ends = []
        for p in self._extracts[1].get_predictions_end(): ends.append(p.n)
        outfile.write(str(starts)+"\n")
        outfile.write(str(ends)+"\n")
        outfile.write(str(self._extracts[1].get_extracts())+"\n")
        outfile.write(str(self._levels[0].get_test_dataset().get_actual_starts())+"\n")
        outfile.write(str(self._levels[0].get_test_dataset().get_actual_ends())+"\n")
        outfile.write(str(self._levels[0].get_test_dataset().get_actual())+"\n")
        outfile.close()

    def print_extractions(self):
        extracted_strings = {}
        ex = {}
        ex2 = {}
        act = {}
        d = self._levels[0].get_test_dataset()
        se_pred =  {'start_l1':{},'end_l1':{},'start_l2':{},'end_l2':{}}
        
        for p in self._extracts[0].get_extracts():
            f_s = d.map_instance_to_file(p[0])
            f_e = d.map_instance_to_file(p[1])
            if f_s != f_e:
                print "XXXXXXXXExtraction crosses documents: "+str(p)
            elif not ex.has_key(f_s):
                ex[f_s] = [p]
            else:
                ex[f_s].append(p)
        for p in self._extracts[1].get_extracts():
            f_s = d.map_instance_to_file(p[0])
            f_e = d.map_instance_to_file(p[1])
            if f_s != f_e:
                print "XXXXXXXXExtraction crosses documents: "+str(p)
            elif not ex2.has_key(f_s):
                ex2[f_s] = [p]
            else:
                ex2[f_s].append(p)
        for p in d.get_actual():
            f_s = d.map_instance_to_file(p[0])
            f_e = d.map_instance_to_file(p[1])
            if f_s != f_e:
                raise "Actual crosses documents: "+str(p)
            if not act.has_key(f_s):
                act[f_s] = [p]
            else:
                act[f_s].append(p)
        for se in ['start','end']:        
            for p in apply(eval('self._extracts[0].get_predictions_'+se)):
                f = d.map_instance_to_file(p.n)
                if not  se_pred[se+'_l1'].has_key(f):
                    se_pred[se+'_l1'][f] = [p]
                else:
                    se_pred[se+'_l1'][f].append(p)
            for p in  apply(eval('self._extracts[1].get_predictions_'+se)):
                f = d.map_instance_to_file(p.n)
                if not  se_pred[se+'_l2'].has_key(f):
                    se_pred[se+'_l2'][f] = [p]
                else:
                    se_pred[se+'_l2'][f].append(p)
        tmp = ex.copy()
        tmp.update(act)
        files = tmp.keys()
        n_files = len(files)
        for tf in files:
            log(2,"\nFile: "+tf+"\n")
            extracted_strings[os.path.split(tf)[-1]]={}
            log(2,"\t"+49*"-"+"\n")
            for pos in act.get(tf,[]):
                log(2,"\tActual:: "+str(pos)+" ")
                tmp =  d.get_tokens(pos[0],pos[1])
                for t in tmp:
                    log(2,t + " ")
                log(2,"\n")
            log(2,"\n\t"+20*"-"+"LEVEL 1"+20*'-'+"\n")
            for pos in ex.get(tf,[]):
                log(2,"\tExtracted :: L1 :: (%d, %d, [%0.3f, %0.3f, %0.3f]) " % (pos[0],pos[1],pos[2][0],pos[2][1],pos[2][2]))
                tmp =  d.get_tokens(pos[0],pos[1])
                extracted_string = ''
                for t in tmp:
                    log(2, t + " ")
                    extracted_string = extracted_string + t + ' '
                log(2,"\n")
                extracted_strings[os.path.split(tf)[-1]][extracted_string.strip()]=pos
            log(2,"\n\tPredictions L1 start: ")
            for s in se_pred['start_l1'].get(tf,[]):
                log(2,str(s)+' ')
            log(2,"\n\tPredictions L1 end  : ")
            for s in se_pred['end_l1'].get(tf,[]):
                log(2,str(s)+' ')
            log(2,"\n")

            log(2,"\n\t"+20*"-"+" LEVEL 2 "+20*'-'+"\n")            
            for pos in ex2.get(tf,[]):
                log(2,"\tExtracted :: L2 :: (%d, %d, [%0.3f, %0.3f, %0.3f]) " % (pos[0],pos[1],pos[2][0],pos[2][1],pos[2][2]))
                tmp =  d.get_tokens(pos[0],pos[1])
                extracted_string = ''
                for t in tmp:
                    log(2, t+" ")
                    extracted_string = extracted_string + t + ' '
                log(2,"\n")
                extracted_strings[os.path.split(tf)[-1]][extracted_string.strip()]=pos
            log(2,"\n")
            log(2,"\n\tPredictions L2 start: ")
            for s in se_pred['start_l2'].get(tf,[]):
                log(2,str(s)+' ')
            log(2,"\n")
            log(2,"\tPredictions L2 end  : ")
            for s in se_pred['end_l2'].get(tf,[]):
                log(2,str(s)+' ')
            log(2,"\n")
            log(2,"\t"+49*"-"+"\n")
        return extracted_strings
        
def usage():
    print "USAGE:     %s datadir traindir testdir" % sys.argv[0]

if __name__ == '__main__':
    try:
        sys.argv[1]
        sys.argv[2]
        sys.argv[3]
    except:
        usage()
        sys.exit()

    e = TwoLevelExtractor(sys.argv[1], 'speaker')
    e.learn(sys.argv[2])
    preds = e.extract(sys.argv[3])
    e.log_extractions()
    e.print_extractions()
    print "Success"

