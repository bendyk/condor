#Setup system for condor
- These scripts will need sudo permissions to install condor correct
- A new user will be created
    user  : "condor" 
    passwd: "condor"
    
1. Download tarballs of condor and pegasus from the official pages or use the attached tarballs
  (Rename tarballs to condor.tar.gz and pegasus.tar.gz)

2. To install Condor only on your local machine execute install_condor.py (use --help option for more information) 

3. To install Condor on a pool of machines execute pusher.py (check condor_pool.ini to setup types and addresses,
   make sure you can password-less login on all machines with correct permissions)

4. To change the Condor type or master of your local machine execute setup_pool.py 
