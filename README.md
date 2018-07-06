# OpenLDAP, back-mdb, and alias dereferencing in large DITs 

This repo contains scripts to set up a demonstration of a problem in
the OpenLDAP slapd. 

## Problem description 

The problem has been described in
http://www.openldap.org/lists/openldap-technical/201805/msg00065.html .

To summarize: When MDB is used as backend databases and with large
DITs (O(10^6)) with many alias entries (O(10^5)),  search requests with
deref=always and scope=sub will take prohibitively long. Servers with
a high request rate might become utterly unresponsive. This is not a
problem with the MDB itself, but rather an algorithmic problem in the
back-mdb library of the slapd. 



## Prerequisites

### Server 
-  A reasonably sized partition  to keep two slapd databases (one
MDB, one HDB)
- enough RAM (8-16GB)

### Software

- A copy of the OpenLDAP git repository. At least the
  slapd/slapadd/slapcat binaries should be available in the
  servers/slapd directory, and the schema definitions in the test
  directory
- python3 in you PATH  
- The python3 ldap3 module




## scripts in ./scripts

### _./scripts/write_tree.py _ 

This python scripts writes a DIT to a slapd running under
ldap://127.0.0.1:1234 

The DIT contains People and property entries, and Groups, where each
group has alias subentries, which point to the people in the group. 

### ./scripts/doit.sh 

Is a bash script which provides configurations for an MDB and HDB
instance of slapd, which starts one instance, calls write_tree.py to
generate a DIT, slapcats/slapadds the DIT to the other instance and
starts that one as well. 

The HDB instance runs then under ldap://127.0.0.1:1234, the MDB
instance under ldap://127.0.0.1:1234 

## How to use it

cd ./scripts 

export OPENLDAP=<path to the openldap repo copy>

bash ./doit.sh

The script will run for a while. In the end two slapds are running
with exactly the same DIT. 

Issue searchrequests like this 

```
 ldapsearch -LLL -x -H ldap://127.0.0.1:1234 -D cn=Manager,ou=test,dc=example,dc=com -w secret -b <search base> -s sub -a always
```
Requests to port 1234 (HDB) might respond slowly (depending on the depth of the search tree under the base) but will return. 

The same request to port 1235 (MDB) will not return and clog up one CPU. 


Request to MDB slapd:

```
time ldapsearch -LLL -x -H ldap://127.0.0.1:1235 -D cn=Manager,ou=test,dc=example,dc=com -w secret -b uid=2000093,ou=Groups,ou=withAliases,ou=test,dc=example,dc=com -s sub -a always dn > /dev/null

real    0m57.343s
user    0m0.000s
sys     0m0.018s
```

Request to HDB slapd:

```
time ldapsearch -LLL -x -H ldap://127.0.0.1:1234 -D cn=Manager,ou=test,dc=example,dc=com -w secret -b uid=2000093,ou=Groups,ou=withAliases,ou=test,dc=example,dc=com -s sub -a always dn > /dev/null

real    0m0.922s
user    0m0.008s
sys     0m0.027s
```

## Patch

The patches to fix the problem are described in README_patches.md. 
