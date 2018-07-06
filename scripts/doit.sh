#!/bin/bash




pref="${OPENLDAP:-$HOME/openldap}"

if  ! [ -x "${pref}/servers/slapd/slapd" ]; then
    cat <<EOF >/dev/stderr
"${pref}/servers/slapd/slapd" not executable

Plese set the OPENLDAP environment variable
to a compiled openldap git repository
EOF
    exit 1
fi

here=$( pwd )
tmp="${here}/tmp"

mkdir -p $tmp

pidfilepref="$tmp/slapd"
mdbpidfile="${pidfilepref}.mdb.pid"
hdbpidfile="${pidfilepref}.hdb.pid"
conffilepref="$here/slapd"
dbdirpref="$here/dbdir"

rm -f "${mdbpidfile}" "${hdbpidfile}"


debug='0'

#trap "{  rm -rf $tmp ; }"  EXIT

function write_config(){
    conffile="$1"
    dbtype="$2"
    dbdirpref="$3"
    dbdir="${dbdirpref}.${dbtype}"
    pidfile="${pidfilepref}.${dbtype}.pid"

    mkdir -p $dbdir
    rm -rf $dbdir/*
    
    cat <<EOF > $conffile
include         $pref/servers/slapd/schema/core.schema
include         $pref/servers/slapd/schema/cosine.schema
include         $pref/servers/slapd/schema/inetorgperson.schema
include         $pref/servers/slapd/schema/openldap.schema
include         $pref/servers/slapd/schema/nis.schema


pidfile         $pidfile
argsfile        $tmp/slapd.1.args
loglevel        0

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


ldiffile="$1"
if [ -n "$ldiffile" ]; then
    if [ -e $ldiffile ] ; then
        $pref/servers/slapd/slapadd -l $ldiffile -b 'ou=test,dc=example,dc=com' -f $hdbconf -q -s 
        $pref/servers/slapd/slapadd -l $ldiffile -b 'ou=test,dc=example,dc=com' -f $mdbconf -q -s 
    fi
fi

$pref/servers/slapd/slapd -f $hdbconf -4 -d $debug -h ldap://127.0.0.1:1234  > $here/hdbslapd.log 2>&1 &


echo -n "waiting for HDB slapd to come up ..."


while ! [ -e $hdbpidfile  ] ; do
    sleep 1
    echo -n .
done

hdbpid=$( cat $hdbpidfile )

trap "{ echo killing $hdbpid ;  kill  $hdbpid ;     rm -rf $tmp ; }"  EXIT
echo
echo "HDB slapd running under pid  $hdbpid port 1234"



if [ -z "$ldiffile"  ]; then
    echo "Building DIT"

    time python3 write_tree.py

    ret=$?
    if [ $ret -ne 0 ] ;then
        exit
    fi

    rm -f "${tmp}/slap.ldif"
    $pref/servers/slapd/slapcat -f $hdbconf -b 'ou=test,dc=example,dc=com' -l "${tmp}/slap.ldif"
    $pref/servers/slapd/slapadd -f $mdbconf -b 'ou=test,dc=example,dc=com' -l "${tmp}/slap.ldif" -s -q
fi

$pref/servers/slapd/slapd -f $mdbconf -4 -d $debug -h ldap://127.0.0.1:1235  > $here/mdbslapd.log 2>&1 &

echo -n "waiting for MDB slapd to come up ..."


while ! [ -e $mdbpidfile  ] ; do
    sleep 1
    echo -n .
done


mdbpid=$( cat $mdbpidfile )
echo
echo "MDB slapd running under pid $mdbpid port 1235"

trap "{ echo killing $hdbpid $mdbpid ;  kill  $hdbpid $mdbpid ;     rm -rf $tmp ; }"  EXIT

wait $mdbpid $hdbpid
