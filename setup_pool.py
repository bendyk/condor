import os
import sys
import time
import subprocess
from optparse import OptionParser


def create_opt_parser():
  parser = OptionParser()

  parser.add_option("-t", "--types", dest="types", action="store",
                    type="string",  default="execute",
                    help="specify machine type ([manager],[submit],[execute])")
  parser.add_option("-m", "--master", dest="master", action="store",
                    type="string",  default="127.0.1.1",
                    help="specify condor master address")

  (options, args) = parser.parse_args()

  if not os.environ.has_key("CONDOR_CONFIG"):
    print("$CONDOR_CONFIG not set")
    exit(-2)
  return options


def change_hostname(options):
  print "change hostname to:"

  with open("/etc/hostname", "w") as f:
    f.write("%s.abc.com" % options.condor_id)
    print "  /etc/hostname"

  new_file = ""
  with open("/etc/hosts", "r") as f:
    for line in f.readlines():
      if "127.0.1.1" in line:
        new_file += "127.0.1.1 %s.abc.com\n" % options.condor_id
      else:
        new_file += line

  with open("/etc/hosts", "w") as f:
    f.write(new_file)
    print "  /etc/hosts"

  os.system("hostname %s.abc.com" % options.condor_id)

  print "hostname changed to %s.abc.com" % options.condor_id



def change_config(options):
#Write Condor config file
  print "reconfigure condor with new config file"
  new_file = ""
  CONDOR_CONFIG = os.environ["CONDOR_CONFIG"]

  with open(CONDOR_CONFIG, "r") as f:
    for line in f.readlines():
      if "use SECURITY :" in line:
        new_file  += "TRUST_UID_DOMAIN = true\n"
        new_file  += "ALLOW_WRITE      = *\n"
        new_file  += "ALLOW_READ       = *\n"

      elif "DAEMON_LIST" in line:
        new_file += create_daemon_list(options.types)

      elif "CONDOR_HOST" in line:
        master = options.master
        if "manage" in options.types:
          master  = "127.0.1.1"
        new_file += "CONDOR_HOST = %s\n" % master

      else:
        new_file  += line
    
  with open(CONDOR_CONFIG, "w") as f:
    f.write(new_file)

#check if condor_master already running
  try:
    subprocess.check_output(["pidof","condor_master"])
  except subprocess.CalledProcessError:
    os.system("%s/sbin/condor_master"   % CONDOR_INSTALL)

  for a in xrange(5):
    print(".")
    time.sleep(1)

  os.system("%s/sbin/condor_reconfig" % CONDOR_INSTALL)


#create daemonlist for config_file
def create_daemon_list(types):
  daemon_list = "DAEMON_LIST = MASTER "
  if "manage" in types:
    daemon_list += "COLLECTOR NEGOTIATOR "
  if "submit" in types:
    daemon_list += "SCHEDD "
  if "execute" in types:
    daemon_list += "STARTD "
  
  return daemon_list + "\n"

 
def main():
  options = create_opt_parser()
#  change_hostname(options)
  change_config(options)
  print "condor configured"

if __name__ == '__main__':
  main()
