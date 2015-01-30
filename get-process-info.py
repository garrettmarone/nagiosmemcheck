#!/bin/python

import getopt,sys,psutil

def usage():
    print "\nUsage: -r warn:crit\n\
          warn:crit can be given as 10mb:100G to throw a warning on any process over 10mb of resident memory usage\n\
          and a critical over 10GB\n"

def main(argv):
    # Parse cmd line options to get mix and max range
    min,max=parseargs()


def parseargs():
    # Define Required cmd line options
    found_r = False
    left=0
    right=0

    try: 
        opts,args = getopt.getopt(sys.argv[1:],"hr:",["help", "range="])

    except getopt.GetoptError as err:
        print(err)
	usage()
        sys.exit(1) # Let's throw a warning for nagios, since we dont want to throw an OK
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(1)  # Same as above
        if o in ('-r', '--range'):
            #print "Range:",a
            found_r = True
            try: 
                left,right=a.split(":",2)
                print left,right
            except ValueError:
                print "\n Couldn't parse the range\n"
                usage()
                sys.exit(1)
            return left,right
    if not found_r:
        print "\n-r or --range is required"
        usage()
        sys.exit(2)
        


def getprocinfo():
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid','name','get_memory_info'])
        except psutil.NoSuchProcess:
            pass
        else:
            print(pinfo)
            print pinfo['memory_info'];
        #if pinfo['memory_info']['vms'] > 100:
        #	print pinfo['name'];
        #else:
        #	pass
    
if __name__ == "__main__" :
    main(sys.argv[1:])
