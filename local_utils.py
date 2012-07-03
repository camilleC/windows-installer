#Ultils to scan local files for Version Information
#@Clark Rinker, June 2012
#@Western Washington University

import re
import _winreg as winkey #Bad? More like that underscore is bad
testPath="C:\\Python27\\README.txt"
vRegex="[0-9]+(?:\.[0-9]+)*"


class AmbiguousMatchError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)


class NoMatchError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)

   
def findVersionInFile(fileString,pattern):
        s=open(fileString()).read()
        matches=re.findall(pattern,s)
        if len(matches)==0:
            raise NoMatchError

        if len(matches>1):
            raise AmbiguousMatchError 
        else:
            return matches[0]
        




#def test():

