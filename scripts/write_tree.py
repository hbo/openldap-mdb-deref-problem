from ldap3 import  *

import re
import collections
import random

host='127.0.0.1'
port=1234
base='ou=test,dc=example,dc=com'

rootdn="cn=Manager,ou=test,dc=example,dc=com"
rootpw="secret"

server = Server(host=host, port=port, use_ssl=False) 
CONN = Connection(server, user=rootdn,password=rootpw)
if not CONN.bind():
    raise Exception("bind failed")

random.seed('Now is the winter of our discontent made glorious summer')

PBASE=1000000
GBASE=1000000
NRPEOPLE=3000
NRGROUPS=2000
NRPROPS=30
MAXGRPSIZE=100

def add_root(root):
    if not CONN.add(dn='{}'.format(root),
                    attributes={
                        'objectClass': ['organizationalUnit'],
                    }
    ):
        raise Exception("could not add root {}:\n{}".format(root, CONN.result))
    


def add_ou(name,parent):
    if not CONN.add(dn='ou={},{}'.format(name,parent),
                    attributes={
                        'objectClass': ['organizationalUnit'],
                    }
    ):
        raise Exception("could not add ou {}:\n{}".format(name, CONN.result))

def add_person(uid,parent,nr_props):
    dn="uid={},{}".format(uid,parent)
    if not CONN.add(dn=dn,
                    attributes={
                        'objectClass': [
                            'person',
                            'inetOrgPerson',
                            'simpleSecurityObject',
                        ],
                        'sn': 'Doe {}'.format(uid),
                        'cn': 'Doe {}, John'.format(uid),
                        'userPassword': 'kanone',
                    }
     ):
        raise Exception("could not add person {} to {}:\n{}".format(uid, parent,CONN.result))
    
    for prop in range(1,nr_props):
        add_ou("somproperty{}".format(prop),dn)

def add_group(gid,parent,members):
    dn="uid={},{}".format(gid,parent)

    if not CONN.add(dn=dn,
                    attributes={
                        'objectClass': [
                            'groupOfNames',
                            'uidObject',
                        ],
                        'cn': 'Group{}'.format(gid),
                        'member': members,
                    }
    ):
        raise Exception("could not add group {} to {}:\n{}".format(gid, parent,CONN.result))
                        
def add_alias(cn,parent,target):
    dn="cn={},{}".format(cn,parent)
    if not CONN.add(dn=dn,
                    attributes={
                        'objectClass': [
                            'alias',
                            'extensibleobject',
                        ],
                        'aliasedObjectName': target,
                    }
    ):
        raise Exception("could not add alias cn={} with target {} to {}:\n{}".format(cn, target, parent,CONN.result))
    

def add_groups(nr_groups,nr_people,parent,peopledn):
    for gid in range(GBASE, GBASE+nr_groups):
        # choose group size between 1 and MAXGRPSIZE
        size=random.randint(1,MAXGRPSIZE)
        # chose starting point
        start=random.randrange(1,nr_people-size)
        # take the consecutive range of people into the group
        members = []
        for member in range(start,start+size):
            m = "uid={},{}".format(member+PBASE,peopledn)

            members = members + [ m ]
        add_group(gid+GBASE,parent,members)
        # add aliases to the people entries
        gdn='uid={},{}'.format(gid+GBASE,parent)
        for member in range(start,start+size):
            pdn='uid={},{}'.format(member+PBASE,peopledn)
            add_alias(member+PBASE,gdn,pdn)
        
     

    
def add_people(nr_people,nr_props, parent):
    for uid in range(PBASE,PBASE+nr_people):
        add_person('{}'.format(uid),parent,nr_props)
    
    
def write_scaffolding():
    add_root('ou=test,dc=example,dc=com')
    add_ou('withAliases', 'ou=test,dc=example,dc=com')
    add_ou('withoutAliases', 'ou=test,dc=example,dc=com')
    add_ou('Groups', 'ou=withAliases,ou=test,dc=example,dc=com')
    add_ou('People', 'ou=withAliases,ou=test,dc=example,dc=com')
    

write_scaffolding()
print("wrote scaffolding")
add_people(NRPEOPLE,NRPROPS,'ou=People,ou=withAliases,ou=test,dc=example,dc=com')
print("added people")
add_groups(NRGROUPS,NRPEOPLE,'ou=Groups,ou=withAliases,ou=test,dc=example,dc=com', 'ou=People,ou=withAliases,ou=test,dc=example,dc=com')
print("added groups")

