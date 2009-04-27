#! /usr/bin/python

import sys,types,os,tempfile,string,popen2
import instances
import utils, config

class twoLevelHistogramTagMatcher:
    def __init__(self, histogram):
        self.histogram = histogram

    def predict_end(self, l1, l2,strategy=1):
        """ l1 and l2 are ExtractionSet objects """
        #Strategy 1: add all L1 predictions and all L2 predictions that occur within 10 toks of start or end
        starts = [l1.get_predictions_start(),l2.get_predictions_start()]
        ends = [l1.get_predictions_end(),l2.get_predictions_end()]
        acc_l2_starts = []
        acc_l2_ends = []
        if strategy==1:
            dist = self.histogram.max_length()
            tmp={}
            #accept a L2 start if an end was predicted in the next dist tokens
            accept={}
            for t in starts[0]:
                tmp[t]=1
            for t in ends[0]:
                accept[t.n]=1
                for a in range(t.n-1,t.n-1-dist, -1):
                    accept[a]=1
            for t in starts[1]:
                if accept.has_key(t.n):
                    tmp[t]=1
                    acc_l2_starts.append(t)
            all_starts = tmp.keys()
            all_starts.sort()

            tmp={}
            #accept L2 end if a start occurred in the previous dist tokens
            accept={}
            for t in ends[0]:
                tmp[t]=1
            for t in starts[0]:
                accept[t.n]=1
                for a in range(t.n+1,t.n+dist+1):
                    accept[a]=1
            for t in ends[1]:
                if accept.has_key(t.n):
                    tmp[t]=1
                    acc_l2_ends.append(t)
            all_ends = tmp.keys()
            all_ends.sort()

            acc_l2_starts.sort()
            acc_l2_ends.sort()
            l2.set_predictions_start(acc_l2_starts)
            l2.set_predictions_end(acc_l2_ends)
            
        elif strategy==2:            
            #Strategy 2: use all L1 and L2 predictions
            tmp={}
            for t in starts[0]+starts[1]:
                tmp[t]=1
            all_starts = tmp.keys()
            all_starts.sort()
            tmp={}
            for t in ends[0]+ends[1]:
                tmp[t]=1
            all_ends = tmp.keys()
            all_ends.sort()

        return self.histogram.predict_end(all_starts, all_ends)



        
class histogramTagMatcher:
    def __init__(self, actuals,overlap=1):
        self.lengths = {}
        self.overlap = overlap
        self.lengths={}
        for a in actuals:
            l = a[1]-a[0]
            if not self.lengths.has_key(l):
                self.lengths[l] = 1
            else:
                self.lengths[l] = self.lengths[l] + 1
        self.n_tags = len(actuals)
    
    def probability(self, length):
        if self.lengths.has_key(length):
            return float(self.lengths[length])/self.n_tags
        else:
            return 0

    def max_length(self):
        return max(self.lengths.keys())+1
    
    def test(self):
        for i in range(10):
            print i,
            print self.probability(i),
            print

    def predict_end(self, starts, ends):
        """ take a list of potential starts and potential ends and return a list of start-end pairs
            returns a tuple of the form (start_token_no, end_token_no, (tag_matcher_confidence, start_tag_confidence, end_tag_confidence)

            # NOTE this greedy search is biased - starts will be unique, but not ends
            # set overlap to force unique starts *and* ends
            # might want to implement a tagmatcher that considers all possibilities combinatorially
        """
        ret = []
        print "preparing to iterate"
        for s in starts:
            best = (0,0,(0,0,0))
            for e in ends:
                if e.n < s.n:
                    pass
                else:
                    p = self.probability(e.n-s.n) 
                    if p > best[2][0]:
                        best = (s.n,e.n,(p,s.confidence,e.confidence))
            if best[2][0]:
                if not self.overlap:
                    for bi in range(len(ret)):
                        if best[0]==ret[bi][0] or best[1]==ret[bi][1]:
                            if self.conf(best) > self.conf(ret[bi]):
                                ret[bi] = best
                                best = ()
                if best:
                    ret.append(best)
        return ret

    def conf(self,pred):
        return pred[2][0]*pred[2][1]*pred[2][2]

