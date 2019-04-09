# OpenLDAP, back-mdb, and alias dereferencing in large DITs 

This repo contains scripts to set up a demonstration of a problem in
the OpenLDAP slapd.  The related bug report is ITS#8875 on the
openldap web page:
https://www.openldap.org/its/index.cgi/Incoming?id=8875 

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
  servers/slapd directory, and the schema definitions in the servers/slapd/schema
  directory
- python3 in your PATH  
- The python3 ldap3 module




## scripts in ./scripts

### ./scripts/write_tree.py  

This python scripts writes a DIT to a slapd running under
ldap://127.0.0.1:1234 

The DIT contains People and property entries, and Groups, where each
group has alias subentries, which point to the respective people
entries of the  group members.

The size of the DIT can be manipulated by setting a couple of
variables to different values:
- NRPEOPLE: Number of people entries in the DIT
- NRGROUPS: Numer of groups created 
- NRPROPS: number of properties associated with each person. They will
  be attached as subentries to the person entry
- MAXGRPSIZE: max size of a group. The actual size is determined
pseudo-randomly. For each group member one alias entry will be added
to the DIT. So approx MAXGRPSIZE * NRGROUPS / 2 will be present in the
generated DIT

With NRPEOPLE the size of the DIT can be influenced without adding
extra aliases.

The current default is
NRPEOPLE=15000
NRGROUPS=3000
NRPROPS=100
MAXGRPSIZE=400



### ./scripts/doit.sh 

Is a bash script which provides configurations for an MDB and HDB
instance of slapd, which starts one instance, calls write_tree.py to
generate a DIT, slapcats/slapadds the DIT to the other instance and
starts that one as well. 

The HDB instance runs then under ldap://127.0.0.1:1234, the MDB
instance under ldap://127.0.0.1:1235 

## How to use it

```
> cd ./scripts 
> export OPENLDAP=<path to the openldap repo copy>
> bash ./doit.sh
```

The script will run for a while (less than an hour on recent
hardware). In the end two slapds are running with exactly the same
DIT.

Issue searchrequests like this 

```
 ldapsearch -LLL -x -H ldap://127.0.0.1:1234 -D cn=Manager,ou=test,dc=example,dc=com -w secret -b <search base> -s sub -a always
```
Requests to port 1234 (HDB) might respond slowly (depending on the depth of the search tree under the base) but will return. 

The same request to port 1235 (MDB) will not return and clog up one CPU. 

## Example

Request to HDB slapd:

```
time clients/tools/ldapsearch -LLL -x -H ldap://127.0.0.1:1234 -D cn=Manager,ou=test,dc=example,dc=com -w secret -b uid=2000093,ou=Groups,ou=withAliases,ou=test,dc=example,dc=com -s sub -a always dn | grep dn: | wc -l 
7601

real    0m0.149s
user    0m0.042s
sys     0m0.048s
```

Request to MDB slapd:

```
time clients/tools/ldapsearch -LLL -x -H ldap://127.0.0.1:1235 -D cn=Manager,ou=test,dc=example,dc=com -w secret -b uid=2000093,ou=Groups,ou=withAliases,ou=test,dc=example,dc=com -s sub -a always dn | grep dn: | wc -l
7601

real    0m22.918s
user    0m0.041s
sys     0m0.021s
```

The MDB slapd needs roughly 150 times longer to serve the same
request.

## Patch

The patches to fix the problem are described in [README_patches.md](README_patches.md). 


