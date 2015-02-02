#!/bin/python
"""

Nagios check script to scan all system processes, and determine if any are outside of the acceptable thresholds
for resident memory vs allocated virtual memory sizes

Author: Garrett Marone <garrett.marone [AT] gmail [DOT] com>
License: MIT

"""

import getopt,sys,psutil

SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}

def usage():
    print "\nUsage: -r warn:crit\n\
          warn:crit can be given as 10M:100G to throw a warning on any process over 10mb of resident memory usage\n\
          and a critical over 100G\n\
          can be given in formats such as 1024B, 100k, 500M, 5G, 10T, 6P, 20Y\n"



def main(argv):
    # Parse cmd line options to get min and max range
    min,max,debug=parseargs()
    if debug: print "\nDebugging output turned on\n"
    if debug: print "Minimum: ",bytes2human(min)," Maximum: ",bytes2human(max)
    warnlist,critlist=procinfocheck(min,max,debug)
    if len(critlist) >= 1:
        print "CRITICAL", critlist
        if (len(warnlist) >= 1): print "WARNING: ",warnlist
        sys.exit(2)
    if len(warnlist) >= 1 and len(critlist) is 0:
        print "WARNING", warnlist
        sys.exit(1)
    print "OK"
    sys.exit(0)
   
   

def procinfocheck(min,max,debug):
    vms=0
    rss=0
    warncount=0
    critcount=0
    critlist=[]
    warnlist=[]

    # Iterate through all processes, and get information
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid','name','get_memory_info'])
        except psutil.NoSuchProcess:
            pass
        else:
            rss,vms=pinfo['memory_info']
            if (rss >= min) and ( rss <= max ):
        	if debug: print pinfo['name'],rss," is greater than",min, "WARN"
                warncount=warncount+1
                warnlist.append({pinfo['name']: bytes2human(rss)})
            elif (rss >= max):
                critcount=critcount+1
                critlist.append({pinfo['name']: bytes2human(rss)})
        	if debug: print pinfo['name'],rss," is greater than",min, "CRIT"
            else:
        	pass
    return warnlist,critlist
    

def parseargs():
    # Define Required cmd line options
    found_r = False
    found_d = False
    lefthuman=0
    righthuman=0
    leftbytes=0
    rightbytes=0

    try: 
        opts,args = getopt.getopt(sys.argv[1:],"hdr:",["help", "debug", "range="])
        #opts,args = getopt.getopt(sys.argv[1:],"hrd:",["help", "range=", "debug"])

    except getopt.GetoptError as err:
        print(err)
	usage()
        sys.exit(1) # Let's throw a warning for nagios, since we dont want to throw an OK
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(1)  # Same as above
        if o in ("-d", "--debug"):
            found_d = True
        if o in ('-r', '--range'):
            found_r = True
            try: 
                lefthuman,righthuman=a.split(":",2)
            except ValueError:
                print "\n Couldn't parse the range\n"
                usage()
                sys.exit(1)
            leftbytes=human2bytes(lefthuman)
            rightbytes=human2bytes(righthuman)
    if not found_r:
        print "\n-r or --range is required"
        usage()
        sys.exit(2)
    if (leftbytes >= rightbytes):
         print "\n Seems that your minimum",leftbytes," is greater than your maximum",rightbytes,"\n\n"
         usage()
         sys.exit(1)
    return leftbytes,rightbytes,found_d
        


def bytes2human(n, format='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs

      >>> bytes2human(0)
      '0.0 B'
      >>> bytes2human(0.9)
      '0.0 B'
      >>> bytes2human(1)
      '1.0 B'
      >>> bytes2human(1.9)
      '1.0 B'
      >>> bytes2human(1024)
      '1.0 K'
      >>> bytes2human(1048576)
      '1.0 M'
      >>> bytes2human(1099511627776127398123789121)
      '909.5 Y'

      >>> bytes2human(9856, symbols="customary")
      '9.6 K'
      >>> bytes2human(9856, symbols="customary_ext")
      '9.6 kilo'
      >>> bytes2human(9856, symbols="iec")
      '9.6 Ki'
      >>> bytes2human(9856, symbols="iec_ext")
      '9.6 kibi'

      >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
      '9.8 K/sec'

      >>> # precision can be adjusted by playing with %f operator
      >>> bytes2human(10000, format="%(value).5f %(symbol)s")
      '9.76562 K'
    """
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776

      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]:1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])


if __name__ == "__main__":
    import doctest
    doctest.testmod()

if __name__ == "__main__" :
    main(sys.argv[1:])
