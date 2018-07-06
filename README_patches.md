# Patches to improve the back-mdb performance in large DITs with
   deref=always and scope=sub

### 0001-Extension-of-dn2id-DB-by-entry-counting-number-of-al.patch

The dn2i database is modified: the "parent id" entries are extended by
one data field "naliases" counting the aliases in their respective
subtrees. The patch contains changes to the mdb_dn2id_add,
mdb_dn2id_delete, mdb_dn2id_delete, mdb_modrdn, and mdb_dn2entry
functions. The change to mdb_dn2entry is require by the necessary
changes in mdb_modrdn, and causes trivial changes in all functions
which call mdb_dn2entry (one more NULL argument has to be added).


### 0002-Adding-mdb_get_aliases-function-to-dn2id.c-replacing.patch

The new function mdb_get_aliases in dn2id.c is a replacement of
mdb_idscope and therefore returns the IDs of aliases in a given search
scope (curscop). The function implements a tree traversal of the
search scope. The code is is copied from mdb_dn2id_walk, and relevant
modifications applied: while mdb_dn2id_walk is an one-step iterator
function to control the tree traversal from outside, mdb_get_aliases
puts the code of mdb_dn2id_walk in a outer for(;;) loop.  IDs of
aliases are identified by looking up the naliases entry in the dn2id
DB. Optimzations are imaginable (pruning subtrees with no aliases from
the traversal) but not implemted here yet.

The naliases entry of the search root id is exploited like this:

- if naliases == 0, mdb_get_aliases returns immediatly with empty
  curscop

- if 0 < naliases < MDB_IDL_DB_SIZE then mdb_get_aliases conducts the
  described tree traversal collecting all aliases and returning them
  in curscop.

- if naliases > MDB_IDL_DB_SIZE and scope=sub, mdb_get_aliases returns
  the IDL range for aliases retreived from the objectClass index. This
  is essentially the same behavior as implemented in mdb_idscope, only
  that it takes orders of magnitude fewer CPU cycles to get there.


## Discussion


The tree traversal in mdb_get_aliases is done with code copied from
mdb_dn2id_walk, put into an outer for() loop and modified to add all
ids of aliases in curscop. One could think of avoiding the code
replication and modify mdb_dn2id_walk itself to take aliases into
account. On the other hand, one could improve the copied code by
mdb_get_aliases by adding a switch where descent into subtrees with
naliases == 0 is avoided. Adding this functionality to mdb_dn2id_walk
might become messy.

When naliases > MDB_IDL_DB_SIZE, it might still be more efficient to
conduct the tree search to get a narrower IDL range. This needs some
experimenting.

The patch improves efficiency of alias dereferencing in the MDB
backend. Not in all cases, although in a high-request-rate scenario
the load of the system will in all likelihood decrease dramatically
(or, view from a different angle, keep the system responsive).
