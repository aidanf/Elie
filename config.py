#!/usr/bin/python
import string,sys

name = "elie"
version = "0.4.1"


#general options
basedir = '/home/aidan/IE/Elie4'
BRILLTAGPATH='/home/aidan/Programming/Brilltag/Bin_and_Data/tagger'
verbosity = 2
java = 'java -mx1900000000 -oss1900000000 '
use_psyco = 0

#learner options are ['knn', 'm5', 'kstar', 'hyper', 'm5rules', 'j48', 'OneR', 'neural', 'winnow', 'LMT', 'jrip', 'SMO', 'prism', 'PART', 'ridor','bayes']
learner = 'SMO'

# options for configuring the tokeniser used in preprocessing
punctuation = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}',
'~']
symbols = ['','$','%','^','*','&','+','=','-','@','~','#','|','\\']
lbrackets = ['(','[','{','<']
rbrackets = [')',']','}','>']
quotes=['"','\'']
longword = 6
usable_tags = ['<sentence>','</sentence>','<paragraph>','</paragraph>']
reserved_characters = {'@':'AT_SYMBOL','"':'DOUBLE_QUOTE','\'':'SINGLE_QUOTE','{':'LEFT_CURLY_BRAC','}':'RIGHT_CURLY_BRAC','%':'PERCENT_SYMBOL','.':'PERIOD',',':'COMMA','?':'QUESTION_MARK'}
special_tokens = {'\n':'xNLx'}

#options for what features the extractor uses
window = 4
m_window = 10
stem = 0
suffix = 0
token = 1
pos = 1
types = 1
gaz = 1
chunk = 1
erc = 1
filter_n_attributes = 5000
filter_threshold = 0
undersample = 50


def describe(description='',outstream=sys.stdout):
    if description:
        print >>outstream, description
    width = 120
    print >>outstream, "Learner: ",learner
    for k in ['window','stem','suffix','token','pos','types','gaz','chunk','erc']:
        print >>outstream,"%s : %s" % (k,eval(k,globals()))
    print >>outstream
    print >>outstream,"Attribute filters:: n_attributes:",str(filter_n_attributes),"threshold:",str(filter_threshold )
    print >>outstream, "Instance filters:: undersample: ",str(undersample)

if __name__=='__main__':
    describe()
