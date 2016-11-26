README

Overview:

Features:
Admin mode:

Polling Station mode:


INSTALLATION:

Windows:
1. Double click EVoting-CSCI6320-FDE.msi
2. Will install to C:\Program Files(x86)\EVoting-CSCI6320-FDE
3. To use in admin mode right click “main.exe” and choose “Run as Administrator”
4. To use as a polling station, run “main.exe” in user mode.

Linux:
1. ?

Mac:
1. ?


BUILD:

Windows:
1. Install Python 3.4
   1. NOTE: will not compile with Python 3.5
   2. Add python install directory to PATH
1. Install PyGI AIO 3.18
   1. Select GTK, Pango, and Glade as install options.
1. Install cx_Freeze, phe from python pip
   1. python -m pip install cx_Freeze
   2. python -m pop install phe
1. Install MySQL python connector
   1. 1. To run from python source
   1. python main.py
1. To build
   1. python setup.py build
   2. exe will be in build/ folder
1. To build installer (msi)
   1. python setup.py bdist_msi
   2. msi will be in bdist*/

Linux:
1. Install dependencies
   1. apt-get install python3 python3-gi python3-pip libmpc-dev libmpfr-dev libgtk-3-dev
1. Install MySQL connector
2. Install phe, cx_Freeze
3. To run from source
   1. python3 main.py
1. To build
   1. python3 setup.py build
1. Installer (? deb)

Mac:
1. ?

setup.sql

CREATE DATABASE evoting;
USE evoting;
CREATE TABLE registered_voters (voter_id INT, first_name CHAR(60) NOT NULL, middle_name CHAR(60) NOT NULL, last_name CHAR(60) NOT NULL, suffix CHAR(4), address VARCHAR(80) NOT NULL, birth DATE NOT NULL, ssn VARCHAR(11), has_voted BOOL, PRIMARY KEY (voter_id));
CREATE TABLE candidates (pres_name VARCHAR(100) NOT NULL, vp_name VARCHAR(100) NOT NULL, party VARCHAR(60) NOT NULL, c_id TINYINT AUTO-INCREMENT NOT NULL, PRIMARY KEY (c_id));
CREATE TABLE votes (unique_id SMALLINT, vote TYPE?? );  //will depend on candidates list

CREATE USER evoting_admin;
GRANT INSERT, DELETE, SELECT, UPDATE on evoting.candidates TO evoting_admin;
GRANT INSERT, DELETE, SELECT, UPDATE on evoting.registered_votersTO evoting_admin;
GRANT SELECT ON evoting.votes TO evoting_admin;

CREATE USER read_candidates;
GRANT SELECT ON evoting.candidates TO ‘read_candidates’;
GRANT INSERT ON evoting.votes TO ‘read_candidates’;
GRANT SELECT (voter_id, first_name, middle_name, last_name, suffix, has_voted) ON evoting.registered_voters TO ‘read_candidates’;
