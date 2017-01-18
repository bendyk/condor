import os
import threading
import getpass
import configparser
from optparse import OptionParser
class Machine:
  

  def __init__(self, machine, default):

    self.master   = machine.getboolean('master' , fallback = False)
    self.machine  = machine.getint(    'id'     , fallback = -1)#
    self.address  = machine.get(       'address', fallback = "")#
    self.types    = machine.get(       'types'  , fallback = default.get('types',  fallback = ""  ))
    self.user     = machine.get(       'user'   , fallback = default.get('user' ,  fallback = ""  ))
    self.tmp_dir  = machine.get(       'tmp_dir'         , fallback = default.get('tmp_dir'       ))
    self.install  = machine.get(       'install_dir'     , fallback = default.get('install_dir'   ))
    self.script   = machine.get(       'script_path'     , fallback = default.get('script_path'   ))
    self.maddr    = machine.get(       'master_address'  , fallback = default.get('master_address'))
    self.cp_files = machine.get(       'transfer_files'  , fallback = default.getboolean('transfer_files',
                                                                                          fallback = False))

    if (self.address == "") or (self.machine == -1):
      print("Error: Check condor_pool.ini no address or id for some machine")
      exit(-1)

  def install_machine(self):
### Use this lines to transfer files if they dont exist on remote hosts
    if self.cp_files:
      self.copy_files()
      self.script = "."

    cmd  = "ssh -oStrictHostKeyChecking=no %s@%s sudo python %s/install_condor.py " %(self.user, self.address, self.script)
    cmd += "-p "    if self.master  else ""
    cmd += "-i %d " % self.machine 
    cmd += "-t %s " % self.types   if self.types   else ""
    cmd += "-m %s " % self.maddr   if self.maddr   else ""
    cmd += "-d %s " % self.install if self.install else ""
    cmd += "--tmp-dir %s " % self.tmp_dir if self.tmp_dir else ""
    print(cmd)
    os.system(cmd)

   
  def copy_files(self):
    cmd  = "scp -oStrictHostKeyChecking=no "
    cmd += self.script + "/install_condor.py "
    cmd += self.script + "/setup_pool.py "
    cmd += self.script + "/condor.tar.gz "
    cmd += self.script + "/pegasus.tar.gz "
    cmd += self.script + "/pegasus_worker.tar.gz "
    cmd += "%s@%s:~" % (self.user, self.address)
    print("----------------------")
    print(cmd)
    os.system(cmd)


  def configure_machine(self):
### Use this lines to transfer files if they dont exist on remote hosts
    if self.cp_files:
      self.copy_files()
      self.script = "."
    cmd  = "ssh -oStrictHostKeyChecking=no %s@%s sudo python %s/setup_pool.py " %(self.user, self.address, self.script)
    cmd += "-t %s " % self.types
    cmd += "-m %s " % self.maddr
    print(cmd)
    os.system(cmd)
    


  
def create_opt_parser():
  parser = OptionParser()

  parser.add_option("-c", "--configure", dest="configure", action="store",
                    default=False,
                    help="Use this option if condor is already installed and \
                          you only want to reconfigure the machines")
  
  (options, args) = parser.parse_args()
  return options


def read_config(machines):
  config = configparser.ConfigParser()
  config.read("condor_pool.ini")

  for section in config.sections():
    if not (section == 'Default'): 
      machines.append(Machine(config[section], config['Default']))

  sorted(machines, key=lambda machine: machine.master)
  

def main():

  threads = []
  machines = []
  read_config(machines)
  options = create_opt_parser()

  for machine in machines:
    if not options.configure:
      threads.append(threading.Thread(target=machine.install_machine, args=[]))
    else:
      threads.append(threading.Thread(target=machine.configure_machine, args=[]))
    threads[-1].start()

    if machine.master:
      threads[-1].join()


  for t in threads:
    t.join()


if __name__ == "__main__":
  main()
