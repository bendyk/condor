import os
import time
from optparse import OptionParser

INSTALL         = "/opt"
CONDOR_INSTALL  = "%s/condor"  % INSTALL
PEGASUS_INSTALL = "%s/pegasus" % INSTALL
CONDOR_CONFIG   = """

"""

def create_opt_parser():
  parser = OptionParser()

  parser.add_option("-i", "--condor-id", dest="condor_id", action="store",
                    type="string",  default="0",
                    help="numeric id of the condor machine")
  parser.add_option("-t", "--types", dest="types", action="store",
                    type="string",  default="execute",
                    help="specify machine type ([manager],[submit],[execute])")
  parser.add_option("-p", "--pegasus", dest="pegasus", action="store_true",
                    default=False,
                    help="additionally install pegasus")
  parser.add_option("--tmp-dir", dest="tmp_dir", action="store",
                    type="string", default="/tmp",
                    help="default temporary directory /tmp/")

  (options, args) = parser.parse_args()

  return options


def install_dependencies():
  print "install java"
  os.system("apt-get --yes --force-yes install openjdk-8-jre openjdk-8-jdk")


def set_env_vars(pegasus):
  print "set env_variables for root, condor and you"
  bin_path = ""

  if pegasus:
    bin_path += ":%s/bin" % PEGASUS_INSTALL 

  bin_path = ":%s/bin" % CONDOR_INSTALL + bin_path
  con_path = "%s/etc/condor_config" % CONDOR_INSTALL

  os.environ["PATH"]         += bin_path
  os.environ["CONDOR_CONFIG"] = con_path

  ENV_VARS = ["PATH+=%s"         % bin_path ,
              "CONDOR_CONFIG=%s" % con_path]

  with open("/root/.bashrc", "a") as f:
    for VAR in ENV_VARS:
      f.write("export %s\n" % VAR)

  with open("/home/condor/.bashrc", "a") as f:
    for VAR in ENV_VARS:
      f.write("export %s\n" % VAR)

  with open("%s/.bashrc" % os.environ["HOME"], "a") as f:
    for VAR in ENV_VARS:
      f.write("export %s\n" % VAR)


def install_condor(types, tmp_dir):
  print "unpack condor"
  os.system("mkdir %s/condor                                  " % tmp_dir)
  os.system("tar -zxvf condor.tar.gz -C %s/condor > /dev/null " % tmp_dir)
  os.system("mv %(tmp)s/condor/*/* %(tmp)s/condor             " % {"tmp": tmp_dir})

  print "install condor to '%s'" % CONDOR_INSTALL
  os.system("mkdir -p %s       " % CONDOR_INSTALL)
  os.system("%s/condor/condor_install \
             --install=%s/condor \
             --install-dir=%s \
             --local-dir=/home/condor \
             --type=%s\
             " % (tmp_dir,tmp_dir,CONDOR_INSTALL,types))


def install_pegasus(tmp_dir):
  print "unpack pegasus"
  os.system("mkdir %s/pegasus                                 " % tmp_dir)
  os.system("tar -zxvf pegasus.tar.gz -C %s/pegasus > /dev/null" % tmp_dir)

  print "install pegasus to '%s'" % PEGASUS_INSTALL
  os.system("mkdir %s                        " % PEGASUS_INSTALL)
  os.system("mv %s/pegasus/pegasus*/* %s " % (tmp_dir, PEGASUS_INSTALL))


def change_hostname(condor_id):
  print "change hostname in:"

  with open("/etc/hostname", "w") as f:
    f.write("condor%s.abc.com" % condor_id)
    print "  /etc/hostname"

  with open("/etc/hosts", "r+") as f:
    new_file = ""
    for line in f.readlines():
      if "127.0.1.1" in line:
        new_file += "127.0.1.1 condor%s.abc.com\n" % condor_id
      else:
        new_file += line

    f.write(new_file)
    print "  /etc/hosts"

  os.system("hostname condor%s.abc.com" % condor_id)

  print "hostname changed to condor%s.abc.com" % condor_id


def check_user():
  print "create new user condor"
  user_exist = False

  with open("/etc/passwd", "r") as f:
    for a in f.readlines():
      if "condor" in a:
        user_exist = True
        condor_id  = a.split(":")[0].split("condor")[1]
        print "Condor user already exist"
        print "Continue with existing user"

  if not user_exist:
    os.system("useradd -d /home/condor -m condor")


def change_config():
  print "reconfigure condor with new config file"
  new_file = ""

  with open("%s/etc/condor_config" % CONDOR_INSTALL, "r") as f:
    for line in f.readlines():
      if "use SECURITY :" in line:
        new_file  += "TRUST_UID_DOMAIN = true\n"
      else:
        new_file  += line
    
  with open("%s/etc/condor_config" % CONDOR_INSTALL, "w") as f:
    f.write(new_file)

#def change_config():
#  print "reconfigure condor with new config file"
#  new_file = ""
#
#  with open("condor_config", "r") as f:
#    for line in f.readlines():
#      new_file += line

#  with open("%s/etc/condor_config" % CONDOR_INSTALL, "r+") as f:
#    part_reached = False
#    for line in f.readlines():
#      if part_reached:
#        new_file += line
#      else:
#        if "-------" in line:
#          part_reached = True
#          new_file += line
#   
#    f.write(new_file)

  os.system("%s/sbin/condor_master"   % CONDOR_INSTALL)
  for a in xrange(5):
    print(".")
    time.sleep(1)
  os.system("%s/sbin/condor_reconfig" % CONDOR_INSTALL)
 
def main():
  options = create_opt_parser()
  check_user()
  change_hostname(options.condor_id)
  install_dependencies()
  install_condor(options.types, options.tmp_dir)
  if options.pegasus:
    install_pegasus(options.tmp_dir)
  set_env_vars(options.pegasus)
  change_config()
  print "system configured"

if __name__ == '__main__':
  main()
