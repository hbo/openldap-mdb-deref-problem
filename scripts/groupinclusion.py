from ldap3 import  *

import re
import collections
import random


NRPEOPLE=1000
NRROLES=1
NRCLEANGROUPS=100
NRMIXGROUPS=100
NRPROPS=100
MAXGRPSIZE=200


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
GMIXBASE=1000000
GCLEANBASE=2000000
RBASE=3000000

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
    

def add_groups(nr_groups,nr_people,parent,peopledn,nr_subgroups):
    if nr_subgroups == 0:
        GBASE = GCLEANBASE
    else:
        GBASE = GMIXBASE
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
        
        sgroups = []
        if nr_subgroups > 0:
            sgsize = random.randint(1,NRCLEANGROUPS)
            sgstart = random.randrange(1,NRCLEANGROUPS-sgsize)
            for sgid in range(sgstart,sgstart+sgsize):
                g = "uid={},{}".format(sgid+GCLEANBASE,parent)
                sgroups = sgroups + [ g ]

        add_group(gid+GBASE,parent,members+sgroups)
        # add aliases to the people entries
        gdn='uid={},{}'.format(gid+GBASE,parent)
        for member in range(start,start+size):
            pdn='uid={},{}'.format(member+PBASE,peopledn)
            add_alias(member+PBASE,gdn,pdn)
        for sgid in range(sgstart,sgstart+sgsize):
            sgdn='uid={},{}'.format(sgid+GCLEANBASE,parent)
            add_alias(sgid+GCLEANBASE,gdn,sgdn)
        

def add_roles(nr_roles, nr_people, nr_mixgroups, nr_cleangroups, parent, gparent, pparent):
    for rid in range(RBASE, RBASE+nr_roles):
        size=random.randint(1,MAXGRPSIZE)
        # chose starting point
        start=random.randrange(1,nr_people-size)
        # take the consecutive range of people into the group
        members = []
        for member in range(start,start+size):
            m = "uid={},{}".format(member+PBASE,peopledn)
            members = members + [ m ]
        

    
def add_people(nr_people,nr_props, parent):
    for uid in range(PBASE,PBASE+nr_people):
        add_person('{}'.format(uid),parent,nr_props)
    
    
def write_scaffolding():
    add_root('ou=test,dc=example,dc=com')
    add_ou('withAliases', 'ou=test,dc=example,dc=com')
    add_ou('Roles', 'ou=withAliases,ou=test,dc=example,dc=com')
    add_ou('Groups', 'ou=withAliases,ou=test,dc=example,dc=com')
    add_ou('People', 'ou=withAliases,ou=test,dc=example,dc=com')
    

write_scaffolding()
print("wrote scaffolding")
add_people(NRPEOPLE,NRPROPS,'ou=People,ou=withAliases,ou=test,dc=example,dc=com')
print("added people")
add_groups(NRCLEANGROUPS,NRPEOPLE,'ou=Groups,ou=withAliases,ou=test,dc=example,dc=com', 'ou=People,ou=withAliases,ou=test,dc=example,dc=com',0)
add_groups(NRMIXGROUPS,NRPEOPLE,'ou=Groups,ou=withAliases,ou=test,dc=example,dc=com', 'ou=People,ou=withAliases,ou=test,dc=example,dc=com',NRMIXGROUPS)
print("added groups")
add_roles(NRROLES,
          NRPEOPLE,
          NRMIXGROUPS,
          NRCLEANGROUPS,
          'ou=Roles,ou=withAliases,ou=test,dc=example,dc=com',
          'ou=Groups,ou=withAliases,ou=test,dc=example,dc=com',
          'ou=People,ou=withAliases,ou=test,dc=example,dc=com')
print("added roles")

