#!/usr/bin/python

import sys

def usage():
    print >>sys.stderr,("%s file1 [file2 file3 ...]"%sys.argv[0])

def average(l):
    """average all the numbers in a list"""
    t = 0
    for a in l:
        t = t + float(a)
    return t/len(l)

class Scorer:
    def __init__(self,predicted='',actual=''):
        self.reset()
        try:
            self.stats['tp']
        except:            
            self.stats = {'tp':0,'fp':0,'fn':0,'fp_partial':0,'fn_partial':0}
        if predicted and actual:
            """predicted and actual are tuples of form (starts, ends, extractions)"""
            for p in predicted[0]:
                self.p_starts[p] = ''
            for p in predicted[1]:
                self.p_ends[p] = ''
            for pr in [ (p[0],p[1]) for p in predicted[2] ]:
                self.p_annots[pr] = ''

            for a in actual[0]:
                self.a_starts[a] = ''
            for a in actual[1]:
                self.a_ends[a] = ''
            for ac in [ (a[0],a[1]) for a in actual[2] ]:
                self.a_annots[ac] = ''

    def reset(self):
        self.p_starts = {}
        self.p_ends = {}
        self.p_annots = {}

        self.a_starts = {}
        self.a_ends = {}
        self.a_annots = {}

        self.scores = {}
        
    def read(self,filename):
        """initialise from a file"""
        f = open(filename)
        p = (eval(f.readline().strip()),eval(f.readline().strip()),eval(f.readline().strip()))
        a = (eval(f.readline().strip()),eval(f.readline().strip()),eval(f.readline().strip()))
        f.close()
        self.__init__(p,a)
        
    def calculate(self):
        fp = 0
        tp = 0
        fn = 0

        fn_partial = 0
        fp_partial = 0
        p = self.p_annots.keys()
        a = self.a_annots.keys()
        p.sort()
        a.sort()
        #print p,"\n\n"
        #print a
        for p in self.p_annots:
            if self.a_annots.has_key(p):
                tp = tp + 1
            else:
                fp = fp + 1
                if self.a_starts.has_key(p[0]) or self.a_ends.has_key(p[1]):
                    fp_partial = fp_partial + 1
        for a in self.a_annots:
            if not self.p_annots.has_key(a):
                fn = fn + 1
                if self.p_starts.has_key(a[0]) or self.p_ends.has_key(a[1]):
                    fn_partial = fn_partial + 1
        try:
            precision = tp/float(tp+fp)
        except ZeroDivisionError:
            precision = 0.0
        try:
            recall = tp/float(tp+fn)
        except ZeroDivisionError:
            recall = 0.0
        try:
            f1 = (2 * precision * recall) / (precision + recall)
        except ZeroDivisionError:
            f1 = 0.0

        self.scores['extracts'] = (precision, recall, f1)
        self.stats['tp'] = self.stats['tp'] + tp
        self.stats['fn'] = self.stats['fn'] + fn
        self.stats['fp'] = self.stats['fp'] + fp
        self.stats['fp_partial'] = self.stats['fp_partial'] + fp_partial
        self.stats['fn_partial'] = self.stats['fn_partial'] + fn_partial
        return (precision*100, recall*100, f1*100)

    def calculate_starts(self):
        fp = 0
        tp = 0
        fn = 0
        for p in self.p_starts:
            if self.a_starts.has_key(p):
                tp = tp + 1
            else:
                fp = fp + 1
        for a in self.a_starts:
            if not self.p_starts.has_key(a):
                fn = fn + 1
        try:
            precision = tp/float(tp+fp)
        except ZeroDivisionError:
            precision = 0.0
        try:
            recall = tp/float(tp+fn)
        except ZeroDivisionError:
            recall = 0.0
        try:
            f1 = (2 * precision * recall) / (precision + recall)
        except ZeroDivisionError:
            f1 = 0.0

        self.scores['starts'] = (precision, recall, f1)
        return (precision, recall, f1)
        
    def calculate_ends(self):
        fp = 0
        tp = 0
        fn = 0
        for p in self.p_ends:
            if self.a_ends.has_key(p):
                tp = tp + 1
            else:
                fp = fp + 1
        for a in self.a_ends:
            if not self.p_ends.has_key(a):
                fn = fn + 1
        try:
            precision = tp/float(tp+fp)
        except ZeroDivisionError:
            precision = 0.0
        try:
            recall = tp/float(tp+fn)
        except ZeroDivisionError:
            recall = 0.0
        try:
            f1 = (2 * precision * recall) / (precision + recall)
        except ZeroDivisionError:
            f1 = 0.0

        self.scores['ends'] = (precision, recall, f1)
        return (precision, recall, f1)
        
    def calculate_sore(self):
        fp = 0
        tp = 0
        fn = 0
        tmp_s = {}
        tmp_e = {}
        for r in self.res:
            for a in r['actual']:
                if r['starts_pred'].has_key(a[0]) or r['ends_pred'].has_key(a[1]):
                    tp = tp + 1
                else:
                    fn = fn + 1
            for p in r['starts_pred']:
                if not r['starts_act'].has_key(p):
                    fp = fp + 1
            for p in r['ends_pred']:
                if not r['ends_act'].has_key(p):
                    fp = fp + 1
                
        try:
            precision = tp/float(tp+fp)
        except ZeroDivisionError:
            precision = 0.0
        try:
            recall = tp/float(tp+fn)
        except ZeroDivisionError:
            recall = 0.0
        try:
            f1 = (2 * precision * recall) / (precision + recall)
        except ZeroDivisionError:
            f1 = 0.0

        self.scores['sore'] = (precision, recall, f1)
        return (precision, recall, f1)

    def error_stats(self):
        tp = self.stats['tp']
        fp = self.stats['fp']
        fn = self.stats['fn']
        
        
        try:
            precision = tp/float(tp+fp)*100
        except ZeroDivisionError:
            precision = 0.0
        try:
            recall = tp/float(tp+fn)*100
        except ZeroDivisionError:
            recall = 0.0
        try:
            f1 = (2 * precision * recall) / (precision + recall)
        except ZeroDivisionError:
            f1 = 0.0

        return """
           Summary

           Extracted Fragments
           
              TP: %d
              FP: %d  - (%d partial)
              FN  %d  - (%d partial)

              
              Precision:   %.3f
              Recall:      %.3f
              F1:          %.3f

           Starts

           Ends

           
        """ % (tp, fp,self.stats['fp_partial'],fn,self.stats['fn_partial'], precision, recall, f1)
        
        
    def __str__(self):
        pass

if __name__ == '__main__':
    try:
        sys.argv[1]
    except:
        usage()
        sys.exit()
    format =  "%-40s  *  %-2.3f %-2.3f %-2.3f  *  %-2.3f %-1.3f %-2.3f  *  %-2.3f %-2.3f %-2.3f"
    print 120*'-'
    print "%-40s  *  %5s %5s %5s  *  %15s  *  %15s" % ("File","Pre","Rec","F1","starts","ends")
    print 120*'-'
    p,p_s,p_e = [],[],[]
    r,r_s,r_e = [],[],[]
    f1,f1_s,f1_e = [],[],[]
    s = Scorer()
    for f in sys.argv[1:]:
        s.read(f)
        a,b,c = s.calculate(),s.calculate_starts(),s.calculate_ends()
        p.append(a[0])
        r.append(a[1])
        f1.append(a[2])
        p_s.append(b[0])
        r_s.append(b[1])
        f1_s.append(b[2])
        p_e.append(c[0])
        r_e.append(c[1])
        f1_e.append(c[2])

        print format % (f,a[0],a[1],a[2],b[0],b[1],b[2],c[0],c[1],c[2])
        s.reset()
    print 120*'-'
    print format % ("Average",average(p),average(r),average(f1),average(p_s),average(r_s),average(f1_s),average(p_e),average(r_e),average(f1_e))
    print 120*'-'
    print s.error_stats()
