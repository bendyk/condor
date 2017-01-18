import os
import sys
import time
import subprocess
from optparse import OptionParser


def create_opt_parser():
  parser = OptionParser()

  parser.add_option("-i", "--condor-id", dest="condor_id", action="store",
                    type="string",  default="0",
                    help="numeric id of the condor machine")
  parser.add_option("-t", "--types", dest="types", action="store",
                    type="string",  default="manager,submit,execute",
                    help="specify machine type ([manager],[submit],[execute]). Default is all types.")
  parser.add_option("-m", "--master", dest="master", action="store",
                    type="string",  default="127.0.1.1",
                    help="specify condor master address")
  parser.add_option("-d", "--install-dir", dest="install_dir", action="store",
                    type="string",  default="/opt",
                    help="specify installation dir for condor [and pegasus]")
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


def set_env_vars(options):
  print "set env_variables for root, condor and you"
  bin_path = ""
  PEGASUS_INSTALL = options.install_dir + "/pegasus"
  WORKER_INSTALL  = options.install_dir + "/worker_pegasus"
  CONDOR_INSTALL  = options.install_dir + "/condor"

  if options.pegasus:
    bin_path += ":%s/bin:%s/bin" % (PEGASUS_INSTALL, WORKER_INSTALL) 

  bin_path = ":%s/bin" % CONDOR_INSTALL + bin_path
  con_path = "%s/etc/condor_config" % CONDOR_INSTALL

  os.environ["PATH"]         += bin_path
  os.environ["CONDOR_CONFIG"] = con_path

  ENV_VARS = ["PATH+=%s"         % bin_path ,
              "CONDOR_CONFIG=%s" % con_path]

  export_to_bashrc("/root/.bashrc", ENV_VARS)
  export_to_bashrc("/home/condor/.bashrc", ENV_VARS)
#  export_to_bashrc("%s/.bashrc" % os.environ["HOME"], ENV_VARS)


def export_to_bashrc(path, ENV_VARS):

  with open(path, "r+") as f:
    exist = False

    for line in f.readlines():
      if "#Condor Environment" in line:
        exist = True

    if not exist:
      f.write("#Condor Environment\n")
      for VAR in ENV_VARS:
        f.write("export %s\n" % VAR)



def install_condor(options):
  types          = options.types
  master         = options.master
  tmp_dir        = options.tmp_dir
  CONDOR_INSTALL = options.install_dir + "/condor"
  tar_path       = "/".join(sys.argv[0].split("/")[0:-1]) if "/" in sys.argv[0] else "."

  if "manage" in types:
    master = "127.0.1.1"

  print "unpack condor"
  
  if not os.path.exists("%s/condor" % tmp_dir):
    os.makedirs("%s/condor" % tmp_dir)
    os.system("tar -zxvf %s/condor.tar.gz -C %s/condor > /dev/null " % (tar_path, tmp_dir))
    os.system("mv %(tmp)s/condor/*/* %(tmp)s/condor             " % {"tmp": tmp_dir})

  print "install condor to '%s'" % CONDOR_INSTALL

  if not os.path.exists(CONDOR_INSTALL):
    os.makedirs(CONDOR_INSTALL)
    os.system("%s/condor/condor_install \
               --install=%s/condor \
               --install-dir=%s \
               --local-dir=/home/condor \
               --central-manager=%s \
               --type=%s\
             " % (tmp_dir,tmp_dir,CONDOR_INSTALL,master,types))
    
    # create condor execution dir
    os.makedirs("/home/condor/config")
    os.chmod("/home/condor/config", 511)
  
  else:
    print "Condor already installed"


def install_pegasus(options):
  tmp_dir  = options.tmp_dir
  PEGASUS_INSTALL = options.install_dir + "/pegasus"
  WORKER_INSTALL  = options.install_dir + "/worker_pegasus"
  tar_path        = "/".join(sys.argv[0].split("/")[0:-1]) if "/" in sys.argv[0] else "."

  print "unpack pegasus"

  if not os.path.exists("%s/pegasus" % tmp_dir):
    os.makedirs("%s/pegasus"        % tmp_dir)
    os.makedirs("%s/worker_pegasus" % tmp_dir)
    os.system("tar -zxvf %s/pegasus.tar.gz -C %s/pegasus > /dev/null"               % (tar_path, tmp_dir))
    os.system("tar -zxvf %s/pegasus_worker.tar.gz -C %s/worker_pegasus > /dev/null" % (tar_path, tmp_dir))

  print "install pegasus to '%s'" % PEGASUS_INSTALL

  if not os.path.exists(PEGASUS_INSTALL):
    os.makedirs(PEGASUS_INSTALL)
    os.makedirs(WORKER_INSTALL)
    os.system("mv %s/pegasus/pegasus*/* %s "        % (tmp_dir, PEGASUS_INSTALL))
    os.system("mv %s/worker_pegasus/pegasus*/* %s " % (tmp_dir, WORKER_INSTALL))
  else:
    print "Pegasus already installed"



def change_hostname(options):
  condor_id = options.condor_id
  print "change hostname in:"

  with open("/etc/hostname", "w") as f:
    f.write("condor%s.abc.com" % condor_id)
    print "  /etc/hostname"

  new_file = ""
  with open("/etc/hosts", "r") as f:
    for line in f.readlines():
      if "127.0.1.1" in line:
        new_file += "127.0.1.1 condor%s.abc.com\n" % condor_id
      else:
        new_file += line

  with open("/etc/hosts", "w") as f:
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
    os.system('useradd -d /home/condor -m condor -p $(echo "condor" | openssl passwd -1 -salt "" -stdin)')


def change_config(options):
#Write Condor config file
  print "reconfigure condor with new config file"
  new_file = ""
  CONDOR_INSTALL = options.install_dir + "/condor"

  with open("%s/etc/condor_config" % CONDOR_INSTALL, "r") as f:
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
          master = "127.0.1.1"
        new_file += "CONDOR_HOST = %s\n" % master

      else:
        new_file  += line
    
  with open("%s/etc/condor_config" % CONDOR_INSTALL, "w") as f:
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
  check_user()
#  change_hostname(options)
  install_dependencies()
  install_condor(options)
  if options.pegasus:
    install_pegasus(options)
  set_env_vars(options)
  change_config(options)
  print "system configured"

if __name__ == '__main__':
  main()
