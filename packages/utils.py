import urllib2,re,calendar, logging,_winreg,ourlogging,platform

from BeautifulSoup import BeautifulSoup

logger = ourlogging.otherLogger("packages.util")




def getPage(url):
    """Returns the contents of a url as a string.

    This currently doesn't do anything to handle exceptions.

    @param url The url to grab a page from.
    @return A string containing the page contents of url.
    """
    try:
        f = urllib2.urlopen(url)
        page = f.read()
        f.close()
    except urllib2.URLError:
        logger.warning("Couldn't not connect to and read from %s" % url)
    except:
        logger.warning('unknown error running  getPage(%s)' % url)
        raise
    else:
        return page
    
def scrapePage(reg, url):
    """Scrapes the page from url for the reg at position pos.

    Returns all matches of reg on page URL. If no matches are found
    and error is returned.

    @param reg The regular expression to match.
    @param url The page to scrape.
    @return The pos'th reg match on the page at url.
    """
    try:
        ret = re.findall(reg, getPage(url), re.IGNORECASE)
    except TypeError as strerror:
        if strerror == 'first argument must be a string or compiled pattern':
            logger.warning('you are missing or have an invalid regex in %s' % reg)
        elif strerror == 'expected string or buffer':
            logger.warning('you have no page being returned by getPage()')
        logger.warning('when calling scrapePage(%s, %s)' %(reg, url))
    except:
        logger.warning('unknown error running  scrapePage(%s, %s)' % (reg, url))
        raise
    else:
        if ret == []:
            logger.warning("No Matches for '%s' found on '%s'" % (reg, url))
            raise IndexError("No Matches found on page")
        return ret
        
def flattenTag(tagList):
    """Strips out HTML tags so that we can process just the text that
    shows up on the screen. Takes in a list of beautiful soup tags and strings.
    Returns a string with the HTML tags stripped out."""
    try:
        if len(tagList.contents) == 1:
            return str(tagList.contents[0])
        else:
            collector = []
            for item in tagList.contents:
                collector += flattenTag(item)
            return "".join(collector)
    except:
        return str(tagList)

def parsePage(reg, url):
    '''Takes in a url. Scans it for <a> tags (links) and returns the one that matches reg.'''
    try:
        f = urllib2.urlopen(url)
        page = f.read()
        soup = BeautifulSoup(str(page))
        f.close()
    except urllib2.URLError:
        logger.warning('Couldn not connect to and read from %s' % url)
    except:
        logger.warning('unknown error running  parsePage(%s)' % url)
        raise
    else:
        #use linkRegex to find useful links, possible downloads
        #Find all of the links on the page
        links = soup.findAll('a')
        correctLinks = []
        #Find all of the links on a page that match reg
        for item in links:
            #itemstr = str(item.contents[0])
            itemstr = flattenTag(item)
            if re.findall(reg, itemstr, re.IGNORECASE) != []:
                correctLinks.append(item)
        if len(correctLinks) > 1:
            #TODO: Handle this error correctly (really is more of a warning, link could be repeated on page)
            logger.warning("More than one download link was found")
            logger.info(correctLinks)
        link = correctLinks[0]['href']
        #The following code handles links correctly don't mess with
        #this unless you know what you are doing
        #A link can come in the following forms:
        # http://foo.bar/absolute/path
        # /relative/to/server/root
        # relative/to/current/path
        if re.findall(".*://.*/", link) != []:
            return link
        else:
            baseURL = url
            #Handle case where url is //foo.bar.com/absolute/path
            #in this case we just need the protocol (http: ftp: etc)
            if link[0:2] == "//":
                baseURL = baseURL.split("/")[0]
                return baseURL + link
            #Handle case where url is absolute /relative/to/server root
            if link[0] == "/":
                baseURL = "/".join(baseURL.split("/")[:3])
                return baseURL + link
            else: #Handle case where url is relative relative/to/current/path
                if baseURL[-1] != "/":
                    baseURL = "/".join(baseURL.split("/")[:-1]) + "/"
                return baseURL + link

        
def downloadFile(URL, directory, fileName):
    """Downloads a given URL to directory
    Returns a dict containing the downloadedPath and 
    the url that was actually downloaded and
    the header data associated with the request:
    {'downloadedPath': downloadPath, 'actualURL': actualURL, 'info':info}"""
    try:
        f = urllib2.urlopen(URL)
        fileContents = f.read()
        actualURL = f.geturl()
        #Get the extension from the url we downloaded
        extension = "." + f.geturl().split(".")[-1]
        info = f.info() #Get the content type and other header info
        f.close()
        #TODO: Clean up the following code, its kinda messy
        downloadpath = directory + '/' + fileName + extension
        if not directory.endswith("/"):
            directory = directory + "/"
        with open(downloadpath, "wb") as downloadedFile:
            downloadedFile.write(fileContents)
        #TODO: End code to be cleaned
        return {'downloadedPath':downloadpath, 'actualURL': actualURL, 'info':info}
    except urllib2.HTTPError, e:
        logger.error("ERROR DOWNLOADING: ", e.code, URL)
        raise
    except urllib2.URLError, e:
        logger.error("URL ERROR: " , e.reason, URL)
        raise
    

def findInString(string, wordList):
    """Checks to see if any of the words in wordList are in string
    returns the first word from wordList that is found in string. Otherwise
    returns false"""
    for word in wordList:
        returnWord = word.upper()
        if string.upper().find(returnWord) != -1:
            return returnWord
    return False
    
def findGreaterCol(a, b):
    """Returns the greater of the two inputs
    Or either if they are equal. A special function
    is needed for this since versions can contain:
    Numbers,ALPHA, BETA, and RC (Release Candidates)"""
    #TODO: Make this handle RC (release canidates)
    aIsNum = False
    bIsNum = False
    try:
        int(a)
        aIsNum = True
    except ValueError:
        aIsNum = False
    try:
        int(b)
        bIsNum = True
    except ValueError:
        bIsNum = False
    if aIsNum and bIsNum:
        if int(a) > int(b):
            return a
        else:
            return b
    elif aIsNum and not bIsNum:
        return a
    elif not aIsNum and bIsNum:
        return b
    else:
        if a.upper() == 'FINAL':
            return a
        elif b.upper == 'FINAL':
            return b
        if a.upper() == 'BETA' and b.upper() == "ALPHA":
            return a
        else:
            return b

def splitOnChars(string, splitChars):
    """Splits a string based upon multiple characters. For example
    splitOnChars('hello-world.foo', '-.') returns:
    ['hello', 'world', 'foo']"""
    collector = [string]
    for char in splitChars:
        temp = []
        for string in collector:
            for item in string.split(char):
                temp.append(item)
        collector = temp
    return collector

def stripChars(string, chars):
    """strips chars from the string string"""
    temp = []
    charset = set(chars)
    for char in string:
        if char in charset:
            temp.append(char)
    return "".join(temp)

def breakVersions(versions):
    """Takes in a list of strings (versions) and returns a list of lists
    where each list represents a version number broken up.
    For example "1.2.3 beta" will become ["1","2","3","BETA"]"""
    versionsSplit = []
    tempVersion = ""
    #Filter out blanks, They are not valid versions
    versions = filter(lambda a: a != '', versions)
    #Filter out invalid chars
    temp = []
    for version in versions:
        version = version.upper()
        stripped = stripChars(version, "1234567890 BETA RC ALPHA.-_")
        temp.append(stripped)
    versionsSplit = temp
    temp = []
    #Break up versions and remove extra white space
    for version in versionsSplit:
        tempstr = splitOnChars(version, ". -_")
        stripped = filter(lambda a: a.strip(), tempstr)
        temp.append(stripped)
    versionsSplit = temp
    temp = []
    #Append FINAL to strings that need it (so 2.2 is a higher version than 2.2 BETA
    for version in versionsSplit:
        hasBetaAlphaRC = findInString(version[-1], ["BETA", "ALPHA", "RC"])
        if not hasBetaAlphaRC:
            version.append("FINAL")
        temp.append(version)
    versionsSplit = temp
    return versionsSplit

def brokenVersionToStr(versions):
    """Takes in a list of broken apart versions and converts them to strings and returns them
    as a list of strings"""
    returnList = []
    for version in versions:
        returnStr = ""
        for element in version:
            if element.isdigit():
                if returnStr != "":
                    returnStr = returnStr + "."
                returnStr = returnStr + element
            elif returnStr != "":
                if element != 'FINAL':
                    returnStr = returnStr + " " + element
            else:
                returnStr = element
        returnList.append(returnStr)
    return returnList

def sanitizeVersions(versions):
    """Takes in a list of versions and removes duplicates and splits
    them into a format sutible for processing"""
    tempList = breakVersions(versions)
    tempList = brokenVersionToStr(tempList)
    tempList = list(set(tempList))
    tempList = breakVersions(tempList)
    return tempList
    
def findHighestVersion(versions):
    	
    """Takes in a list of strings and returns the highest version formatted in a standard format:
    1.2.3 [ALPHA|BETA|RC[0-9]]"""
    # Make sure to sanitize 
    tempList = sanitizeVersions(versions)
    return findHighestVersionHelper(tempList,0)
    
def findHighestVersionHelper(versions, col):
    #Don't mess with the following code. If there is a problem sorting
    #versions then the function findGreaterCol probably has a bug.
    #In other words: Here there be dragons, don't mess with them
    #unless you know what you are doing.
    if len(versions) == 1:
        return brokenVersionToStr(versions)[0]
    else:
        maxVer = "0"
        for element in versions:
            maxVer = findGreaterCol(maxVer,element[col])
        returnList = []
        for element in versions:
            if element[col] == maxVer:
                returnList.append(element)
        return findHighestVersionHelper(returnList,col + 1)

		
def getInstalledRegvalSearchUninstallVersion(pak):
    """
    Searches a Regsitry Entries's Values and and searches the data entry for the given regex
    This function also will search all of the subkeys of a key as well as the key itself
    In order to handle the case of searching SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall
    Where Key names themselves can be cryptic, making it hard to find installed Versions
    """
    if(platform.machine =='i386'):
        if (pak.arch=='x86_64'):
            return None
        else:
            mask=_winreg.KEY_READ
    else:
        if pak.arch=='x86_32':
            mask=_winreg.KEY_READ|_winreg.KEY_WOW64_32KEY
        elif pak.arch=='x86_64':
            mask= _winreg.KEY_READ|_winreg.KEY_WOW64_64KEY
        else:
            print "sorry not implemented"
            return None
    try:
    
        # should do a lookup table here
        if pak.regKey == 'HKLM':
            un = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, pak.regSubKey,0,mask)
        else:
            return None

        unlen = _winreg.QueryInfoKey(un)[0]
        for i in range(unlen):
           
            key=_winreg.OpenKey(un,_winreg.EnumKey(un,i))
            #for each subkey of uninstall enum it's values
            vallen=_winreg.QueryInfoKey(key)[1]
            for j in range(vallen):
                value=_winreg.EnumValue(key,j)
                if value[0]==pak.regValue and re.search(pak.regRegEx,value[1])!=None:
                    version=re.search(pak.regRegEx,value[1]).group(0)
                    return version



        #Do it again, in case it isn't a subkey
        vallen=_winreg.QueryInfoKey(un)[1]
        for j in range(vallen):
            value=_winreg.EnumValue(un,j)
            if value[0]==pak.regValue and re.search(pak.regRegEx,value[1])!=None:
                version=re.search(pak.regRegEx,value[1]).group(0)
            
                return version
        return None
                
       

    except TypeError as strerror:
        if strerror == 'first argument must be a string or compiled pattern':
            logger.debug('you are missing or have an invalid regex')
        elif strerror == 'expected string or buffer':
            logger.debug('your have no value being pulled from the registry')
          
    except WindowsError:
        logger.debug('The registry key or value could not be found')
      
    except KeyError as strerror:
        logger.debug('did not contain a key entry')
       
    except Exception as e:
        logger.debug(str(e))
    else:
        return None
 
def getInstalledRegkeyVersion(pak):
    """Get the version of the installed package from a registry value.
    Use the information specified in the package d to lookup the installed
    version on the computer.

    @param d A installversion dictionary entry for a package containing at
    least entries for 'key', 'subkey', 'regex', and 'regexpos'
    @return The version installed or None.
    """
    if(platform.machine =='i386'):
        if (pak.arch=='x86_64'):
            return None
        else:
            mask=_winreg.KEY_READ
    else:
        if pak.arch=='x86_32':
            mask=_winreg.KEY_READ|_winreg.KEY_WOW64_32KEY
        elif pak.arch=='x86_64':
            mask= _winreg.KEY_READ|_winreg.KEY_WOW64_64KEY
        else:
            print "sorry not implemented"
            return None
            
    try:
    
        # should do a lookup table here
        if pak.regKey == 'HKLM':
            tempkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, pak.regSubKey,0,mask)
        else:
            return None

        keys = _winreg.QueryInfoKey(tempkey)[0]
        keynames = sorted([_winreg.EnumKey(tempkey,i) for i in xrange(keys)])
        keynamesstr = "\n".join(keynames)
        version = re.findall(pak.regRegEx, keynamesstr)[int(pak.regExPos)]
        return version

    except TypeError as strerror:
        if strerror == 'first argument must be a string or compiled pattern':
            logger.debug('you are missing or have an invalid regex')
        elif strerror == 'expected string or buffer':
            logger.debug('your have no value being pulled from the registry')
          
    except WindowsError:
        logger.debug('The registry key or value could not be found')
      
    except KeyError as strerror:
        logger.debug('did not contain a key entry')
       
    except Exception as e:
        logger.debug(str(e))
    else:
        return None

def getInstalledRegvalnameVersion(pak):
    """Get the version of the installed package from a registry value.

Use the information specified in the package d to lookup the installed
version on the computer.

@param d A installversion dictionary entry for a package containing at
least entries for 'key', 'subkey', 'regex', and 'regexpos'
@return The version installed or None.
"""
    if(platform.machine =='i386'):
        if (pak.arch=='x86_64'):
            return None
        else:
            mask=_winreg.KEY_READ
    else:
        if pak.arch=='x86_32':
            mask=_winreg.KEY_READ|_winreg.KEY_WOW64_32KEY
        elif pak.arch=='x86_64':
            mask= _winreg.KEY_READ|_winreg.KEY_WOW64_64KEY
        else:
            print "sorry not implemented"
            return None
    try:
        # should do a lookup table here
        if pak.regKey == 'HKLM':
            tempkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, pak.regSubKey,0,mask)
        else:
            return None
        vals = _winreg.QueryInfoKey(tempkey)[1]
        valnames = [_winreg.EnumValue(tempkey,i)[0] for i in xrange(vals)]
        valnames = sorted(valnames)#Does This work?
        valnamesstr = "\n".join(valnames)
        version = re.findall(pak.regRegEx, valnamesstr)[int(pak.regExPos)]
        return version

    except TypeError as strerror:
        if strerror == 'first argument must be a string or compiled pattern':
            logger.debug('you are missing or have an invalid regex')
        elif strerror == 'expected string or buffer':
            logger.debug('your have no value being pulled from the registry')
          
    except WindowsError:
        logger.debug('The registry key or value could not be found')
      
    except KeyError as strerror:
        logger.debug('did not contain a key entry')
       
    except Exception as e:
        logger.debug(str(e))
    else:
        return None


def getInstalledRegvalVersion(pak):
    """Get the version of the installed package from a registry value.

Use the information specified in the package d to lookup the installed
version on the computer.

@param d A installversion dictionary entry for a package containing at
least entries for 'key', 'subkey', 'value', 'regex', and 'regexpos'
@return The version installed or None.
"""
    if(platform.machine =='i386'):
        if (pak.arch=='x86_64'):
            return None
        else:
            mask=_winreg.KEY_READ
    else:
        if pak.arch=='x86_32':
            mask=_winreg.KEY_READ|_winreg.KEY_WOW64_32KEY
        elif pak.arch=='x86_64':
            mask= _winreg.KEY_READ|_winreg.KEY_WOW64_64KEY
        else:
            print "sorry not implemented"
            return None
    try:
        
        # should do a lookup table here
        if pak.regKey == 'HKLM':
            tempkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, pak.regSubKey,0,mask)
            value = str(_winreg.QueryValueEx(tempkey, pak.regValue)[0])

            print re.findall(pak.regRegEx, value)
            version = re.findall(pak.regRegEx, value)[int(pak.regExPos)]
           
          
            return version
        else:
            return None
    except TypeError as strerror:
        if strerror == 'first argument must be a string or compiled pattern':
            logger.debug('you are missing or have an invalid regex')
        elif strerror == 'expected string or buffer':
            logger.debug('your have no value being pulled from the registry')
          
    except WindowsError:
        logger.debug('The registry key or value could not be found')
      
    except KeyError as strerror:
        logger.debug('did not contain a key entry')
       
    except Exception as e:
        logger.debug(str(e))
    else:
        return None

	

def getInstalledFileVersion(pak):
    filepath=pak.localVersionFilePath
    regex=pak.localVersionFileRegex
    #print filepath,regex
    """filepath,regex
    Retrives Version info from a file
    Takes a string filepath and a string regex to match
    Returns the version number if Found
    Returns None if No matches are found, too many machs are found
    """

    try:

        s=open(filepath).read()
        matches=re.search(regex,s)
        return matches.group(0)

    except Exception:
        return


		
		
def findInstalledVersions(pak):
    """Takes in a package and attempts to find the installed version(s) If the package is installed."""
    #TODO: Fill in this function
    #Qtype regkey regval regvalsearch regvalname
    print pak.regQueryType
    if pak.regQueryType =="regkey":

        return getInstalledRegkeyVersion(pak)
        
    elif pak.regQueryType =="regval":
        print("Finding By Regval")
        return getInstalledRegvalVersion(pak)

    elif pak.regQueryType =="regvalname":
        return getInstalledRegvalnameVersion(pak)

    elif pak.regQueryType=="regvalsearch":
        return getInstalledRegvalSearchUninstallVersion(pak)
        

    #If they do not specify registery info then you need to search the filesystem
    elif pak.localVersionFilePath !="":
        return getInstalledFileVersion(pak)

    else:
        return None

        
    
def findVersionsReg(pak):
    """Takes in a package and attempts to find version(s) in the registry"""
    # Attempt to find the version in the Uninstall Directory of the registry
    #TODO: Implement this function
    print "Sorry THis appears to be a stub"
