import os
import threading
import getpass
import configparser

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

  def start_server(self):
    if self.cp_files:
      self.copy_files()
      self.script = "."

    cmd  = "ssh %s@%s python %s/setup_system.py " %(self.user, self.address, self.script)
    cmd += "-p "    if self.master  else ""
    cmd += "-i %d " % self.machine 
    cmd += "-t %s " % self.types   if self.types   else ""
    cmd += "-m %s " % self.maddr   if self.maddr   else ""
    cmd += "-d %s " % self.install if self.install else ""
    cmd += "--tmp-dir %s " % self.tmp_dir if self.tmp_dir else ""
    print(cmd)
    os.system(cmd)

   
  def copy_files(self):
    cmd  = "scp "
    cmd += self.script + "/setup_system.py "
    cmd += self.script + "/condor.tar.gz "
    cmd += self.script + "/pegasus.tar.gz "
    cmd += self.script + "/pegasus_worker.tar.gz "
    cmd += "%s@%s:~" % (self.user, self.address)
    print("----------------------")
    print(cmd)
    os.system(cmd)

      


def read_config(machines):
  config = configparser.ConfigParser()
  config.read("condor_pool.ini")

  for section in config.sections():
    if not (section == 'Default'): 
      machines.append(Machine(config[section], config['Default']))

  sorted(machines, key=lambda machine: machine.master)
  

def main():

  machines = []
  read_config(machines)

  for machine in machines:
    print("start Machine %d" % machine.machine)
    t = threading.Thread(target=machine.start_server, args=[])
    t.start()
    if machine.master:
      t.join()


if __name__ == "__main__":
  main()
