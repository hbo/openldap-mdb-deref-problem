#!/bin/bash


pref="$HOME/software/openldap"

tmp=$( mktemp -d )
tmp=$( mktemp -d )
here=$( pwd )

pidfilepref="$tmp/slapd"
mdbpidfile="${pidfilepref}.mdb.pid"
hdbpidfile="${pidfilepref}.hdb.pid"
conffilepref="$here/slapd"
dbdirpref="$here/dbdir"

debug='trace,stats'

trap "{  rm -rf $tmp ; }"  EXIT

function write_config(){
    conffile="$1"
    dbtype="$2"
    dbdirpref="$3"
    dbdir="${dbdirpref}.${dbtype}"
    pidfile="${pidfilepref}.${dbtype}.pid"

    mkdir -p $dbdir
    rm -rf $dbdir/*
    
    cat <<EOF > $conffile
include         $pref/tests/schema/core.schema
include         $pref/tests/schema/cosine.schema
include         $pref/tests/schema/inetorgperson.schema
include         $pref/tests/schema/openldap.schema
include         $pref/tests/schema/nis.schema
include         $pref/tests/testdata/test.schema

pidfile         $pidfile
argsfile        $tmp/slapd.1.args

sockbuf_max_incoming 4194303

database        monitor


database        $dbtype
suffix          "ou=test,dc=example,dc=com"
rootdn          "cn=Manager,ou=test,dc=example,dc=com"
rootpw          secret
directory       $dbdir
index           objectClass     eq
index           cn,sn,uid       pres,eq,sub
dbnosync        true
EOF
    case $dbtype in
        mdb)
           cat <<EOF >> $conffile
maxsize 17179869184
EOF

        ;;
        hdb)
            cat <<EOF > $dbdir/DB_CONFIG
set_cachesize 16 0 1
set_lg_bsize 2097152
set_lk_max_locks 1000000
set_lk_max_objects 1000000
set_lk_max_lockers 1000000
set_lg_dir $here/hdblog
set_flags DB_LOG_AUTOREMOVE
EOF
            mkdir -p $here/hdblog
        ;;
        *)
        ;;
    esac
}
mdbconf="${conffilepref}.mdb.conf"
hdbconf="${conffilepref}.hdb.conf"
write_config    $mdbconf mdb $dbdirpref
write_config    $hdbconf hdb $dbdirpref


ldiffile=
if [ $# -gt  0 ]; then
    ldiffile="$1"
    if [ -e $ldiffile ] ; then
        $pref/servers/slapd/slapadd -l $ldiffile -b 'ou=test,dc=example,dc=com' -f $mdbconf -q -s 
        $pref/servers/slapd/slapadd -l $ldiffile -b 'ou=test,dc=example,dc=com' -f $hdbconf -q -s 
    fi
    exit
fi

$pref/servers/slapd/slapd -f $conffile -4 -d $debug -h ldap://127.0.0.1:1234  > $here/slapd.log 2>&1 &

sleep 2

pid=$( cat $pidfile )

trap "{ echo killing $pid ;  kill  $pid ;     rm -rf $tmp ; }"  EXIT
echo slapd running under $pid

if [ -z "$ldiffile"  ]; then 
    time python3 write_tree.py
fi

wait $pid
