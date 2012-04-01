"""Monitor server processes.

This module grew out of Webfaction's `autostart.cgi` file, which is placed in
a new web application when created from the control panel.  It can be used
in any situation where a file checker is needed.

To use, replace your `autostart.cgi` file with something like this:

from reynard.monitor import check

if __name__ == '__main__':
    BASEDIR = os.path.dirname(__file__)
    ENVIRONMENT = os.path.join(BASEDIR, 'env')

    DAEMON = os.path.join(ENVIRONMENT, 'bin/cherryd')
    ARGS = '-i website -c production.ini'

    check(BASEDIR, DAEMON, ARGS)
"""
import os
import subprocess

def check(basedir, daemon, args, pidfile=None):
    "Restart `daemon` if not running."
    
    if pidfile is None:
        pidfile = os.path.join(basedir, 'pid')

    # Test if the process is already running
    running = False

    try:
        # Try to read pid file
        pid = open(pidfile).read()

        # Check if this process is up
        lines = os.popen('ps -p %s' % pid).readlines()
        
        if len(lines) > 1:
            running = True
        else:
            # Delete pid file
            os.remove(pidfile)

    except IOError:
        pass

    print "Content-type: text/html\r\n"
    if running:
        print """<html><head>
<META HTTP-EQUIV="Refresh" CONTENT="2; URL=.">
</head>
<body>
    Site is starting ...<a href=".">click here<a>
</body>
</html>"""
    else:
        print """<html><head>
<META HTTP-EQUIV="Refresh" CONTENT="2; URL=.">
</head>
<body>
    Restarting site ...<a href=".">click here<a>
</body>
</html>"""
        
        process = subprocess.Popen("%s -i website -c production.ini" % daemon,
                                   shell=True,
                                   stdout=subprocess.PIPE)

        open(pidfile, 'w').write(str(process.pid))
        
