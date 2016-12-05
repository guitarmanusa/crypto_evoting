README
======
![Polling Station - Pg 1 - Welcome](screenshots/Pg 1 - Welcome.jpg?raw=true "Pg 1 - Welcome")
![Polling Station - Pg 2 - Privacy](screenshots/Pg 2 - Privacy.jpg?raw=true "Pg 2 - Privacy")
![Polling Station - Pg 3 - Voter Fraud](screenshots/Pg 3 - Voter Fraud.jpg?raw=true "Pg 3 - Voter Fraud")
![Polling Station - Pg 4 - Voter ID](screenshots/Pg 4 - Voter ID.jpg?raw=true "Pg 4 - Voter ID")
![Polling Station - Pg 5 - Candidates](screenshots/Pg 5 - Candidates.jpg?raw=true "Pg 5 - Candidates")
![Polling Station - Pg 6 - Confirmation](screenshots/Pg 6 - Confirmation.jpg?raw=true "Pg 6 - Confirmation")
![Polling Station - Pg 7 - ZKP](screenshots/Pg 7 - ZKP.jpg?raw=true "Pg 7 - ZKP")
![Polling Station - Pg 8 - I Voted](screenshots/Pg 8 - I Voted.jpg?raw=true "Pg 8 - I Voted")
![Admin - About](/screenshots/Admin - About.jpg?raw=true "Admin - About")
![Admin - Login](screenshots/Admin Pg 1 - Login.jpg?raw=true "Admin - Login")
![Admin - Candidates](screenshots/Admin - Candidates.jpg?raw=true "Admin - Candidates")
![Admin - Voters](screenshots/Admin - Voters - Add.jpg?raw=true "Admin - Voters")
![Admin - Results](screenshots/Admin - Results.jpg?raw=true "Admin - Results")


Overview:
---------
An example implementation of an e-voting system using Paillier's homomorphic encryption.
To ensure that the malleability property of the Paillier system is not abused to provides
false votes a Zero Knowledge Interactive Proof (ZKIP) is utilized.  The ZKIP agent (BB_and_EM.py)
is currently running on the same remote server as the MySQL DB.  This system is cross platform
by utilizing Python and GTK.
###Features:
####Admin mode:
- Authentication as an an administrator to the MySQL backend utilizes SHA256 passwords
- Add/Delete Candidates for Election
- Add/Edit/Delete/Find voters
- Calculate election results
- About Menu
- Demo version administrator credential
    user: evoting_admin
    pass: testTEST0192)!(@

####Polling Station mode:
- Connection to MySQL database backend is encrypted (email franck6@rpi.edu for requisite ca.pem, ca.key, and ca.cert files)
- Connection between polling station and Election Registrar (EM) that engages in ZKIP is encrypted with TLS.
- Votes are encrypted utilizing the Paillier's homomorphic public key system so that identical votes are indistinguishable from each other.
- Utilizes

INSTALLATION:
=============

Windows:
--------
1. Double click EVoting-CSCI6320-FDE.msi
2. Will install to C:\Program Files(x86)\EVoting-CSCI6320-FDE
3. Copy ca.pem, ca.key, ca.cert to C:\Program Files(x86)\EVoting-CSCI6320-FDE\
4. To use in admin mode right click “main.exe” and choose “Run as Administrator”
5. To use as a polling station, run “main.exe” in user mode.

Linux:
------
1. Clone git repo
2. Copy ca.pem, ca.key, ca.cert into crypto_evoting
3. To run in admin mode:
    sudo python3 main.py
4. To run in polling station mode:
    python3 main.py

Mac:
----
1. TODO


BUILD:
======
Windows:
--------
1. Install [Python 3.4](https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi)
   1. NOTE: will not compile with Python 3.5
   2. Add python install directory to PATH
      1. C:> PATH=$PATH;<Python 3.4 install dir>
2. Install [PyGI AIO 3.18](https://sourceforge.net/projects/pygobjectwin32/files/latest/download)
   1. Select GTK, Pango, and Glade as install options.
      1. For a dev environment, selecting "DevHelp" is recommended
3. Install cx_Freeze, phe, pycrypto from python pip
   1. python -m pip install cx_Freeze
   2. python -m pop install phe
      1. Read about phe and it's pallier implementation [https://python-paillier.readthedocs.io/en/stable/](https://python-paillier.readthedocs.io/en/stable/)
4. Install MySQL python connector
   1. [Windows (x86, 32bit), MSI Installer, Python 3.4](https://dev.mysql.com/downloads/connector/python/2.1.html)
5. Clone repo
   1. git clone https://github.com/guitarmanusa/crypto_evoting
6. To run from python source ("dev environment")
   1. python BB_and_EM.py
      1. This runs the ZKP agent in the background, can also change IP address to 159.203.140.245
   2. python main.py
7. To build
   1. python setup.py build
   2. exe will be in build/ folder
8. To build installer (msi)
   1. python setup.py bdist_msi
      Note: .msi will be in bdist*/

Linux:
1. Install dependencies
   1. # apt-get install python3 python3-gi python3-pip libmpc-dev libmpfr-dev libgtk-3-dev
2. Install MySQL connector
   1. http://dev.mysql.com/downloads/connector/python/
3. Install phe, cx_Freeze, pycrypto (python3 -m pip install ...)
   1. To run from source
      1. python3 BB_and_EM.py &
         1. This runs the ZKP agent in the background, can also change IP address to 159.203.140.245
      2. python3 main.py
   2. To build (TODO)
      1. python3 setup.py build
4. Installer (TODO write setup.py for linux)

Mac:
1. ?

setup.sql

CREATE DATABASE evoting;

USE evoting;

CREATE TABLE registered_voters (voter_id BIGINT, first_name CHAR(60) NOT NULL, middle_name CHAR(60) NOT NULL, last_name CHAR(60) NOT NULL, suffix CHAR(4), address VARCHAR(80) NOT NULL, birth DATE NOT NULL, ssn VARCHAR(11), has_voted BOOL, PRIMARY KEY (voter_id));

CREATE TABLE candidates (pres_name VARCHAR(100) NOT NULL, vp_name VARCHAR(100) NOT NULL, party VARCHAR(60) NOT NULL, c_id TINYINT AUTO_INCREMENT NOT NULL, PRIMARY KEY (c_id));

CREATE TABLE votes (voter_id BIGINT NOT NULL, ctxt VARCHAR(1400) NOT NULL, c_id TINYINT NOT NULL, PRIMARY KEY (voter_id, c_id));

CREATE TABLE private_key (lambda VARCHAR(1400), mu VARCHAR(1400));

CREATE USER evoting_admin;  
GRANT INSERT, DELETE, SELECT, UPDATE on evoting.candidates TO evoting_admin;  
GRANT INSERT, DELETE, SELECT, UPDATE on evoting.registered_votersTO evoting_admin;  
GRANT SELECT ON evoting.votes TO evoting_admin;

CREATE USER read_candidates;  
GRANT SELECT ON evoting.candidates TO ‘read_candidates’;  
GRANT INSERT ON evoting.votes TO ‘read_candidates’;  
GRANT SELECT (voter_id, first_name, middle_name, last_name, suffix, has_voted) ON evoting.registered_voters TO ‘read_candidates’;
GRANT SELECT ON private_key TO 'evoting_admin';
GRANT SELECT (ctxt, c_id) ON votes TO 'evoting_admin'
