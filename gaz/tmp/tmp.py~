import sys
sys.path.append('/home/aidan/IE/Elie2/')
import tagging

f = open(sys.argv[1])
words = {}
for line in f:
    if line:
        word = line.split()[0]
        word = word.strip().lower()
        words[word]=1

f2 = f = open(sys.argv[2])
for line in f2:
    word = line.strip().lower()
    words[word] = 1

for word in words.keys():
    print word
#for w in words.keys():
#    print w
"""
f = open('speakers.txt')
for line in f:
        line = line.strip()
        if line:
            name = line.split(':')[1]
            tmp = name.split()
            first,last = tmp[0],tmp[-1]
            print last
"""
