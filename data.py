#############################################################################
# ParaTrac: Scalable Tracking Tools for Parallel Applications
# Copyright (C) 2009  Nan Dun <dunnan@yl.is.s.u-tokyo.ac.jp>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

#
# Data persistence
#

__all__ = ["Database", "FUSETracDB"]

import sys
import os
import sqlite3
import csv
import numpy

class Database:
    def __init__(self, dbfile):
        self.dbfile = os.path.abspath(dbfile)
        self.db = sqlite3.connect(self.dbfile)
        self.cur = self.db.cursor()
    
    def __del__(self):
        if self.db is not None:
            self.db.commit()
            self.db.close()

    def close(self):
        self.db.commit()
        self.db.close()
        self.db = None

    def cursor(self):
        return self.db.cursor()

class FUSETracDB(Database):
    def create_tables(self):
        cur = self.cur
        # table: env
        cur.execute("DROP TABLE IF EXISTS env")
        cur.execute("CREATE TABLE IF NOT EXISTS env "
            "(item TEXT, value TEXT)")

        # table: syscall
        cur.execute("DROP TABLE IF EXISTS syscall")
        cur.execute("CREATE TABLE IF NOT EXISTS syscall "
            "(stamp DOUBLE, pid INTEGER, sysc INTEGER, fid INTEGER, "
            "res INTEGER, elapsed DOUBLE, aux1 INTEGER, aux2 INTEGER)")

        # table: file
        cur.execute("DROP TABLE IF EXISTS file")
        cur.execute("CREATE TABLE IF NOT EXISTS file"
            "(fid INTEGER, path TEXT)")
        
        # table: proc
        cur.execute("DROP TABLE IF EXISTS proc")
        cur.execute("CREATE TABLE IF NOT EXISTS proc "
            "(pid INTEGER, ppid INTEGER, live INTEGER, res INTEGER, "
            "btime FLOAT, elapsed FLOAT, cmdline TEXT)")

    def import_data(self, datadir=None):
        if datadir is None:
            datadir = os.path.dirname(self.dbfile)

        cur = self.cursor()
        
        # import runtime environment data
        envFile = open("%s/env.log" % datadir)
        assert envFile.readline().startswith("#")
        for line in envFile.readlines():
            cur.execute("INSERT INTO env VALUES (?,?)", 
                line.strip().split(":", 1))
        envFile.close()
        
        # import trace log data
        traceFile = open("%s/trace.log" % datadir)
        assert traceFile.readline().startswith("#")
        for line in traceFile.readlines():
            cur.execute("INSERT INTO syscall VALUES (?,?,?,?,?,?,?,?)",
                line.strip().split(","))
        traceFile.close()

        # import file map data
        filemapFile = open("%s/file.map" % datadir)
        assert filemapFile.readline().startswith("#")
        for line in filemapFile.readlines():
            cur.execute("INSERT INTO file VALUES (?,?)",
                line.strip().split(":", 1))
        filemapFile.close()

        # import proc info data
        procmapFile = open("%s/proc.map" % datadir)
        assert procmapFile.readline().startswith("#")
        procmap = {}
        lineno = 0
        for line in procmapFile.readlines():
            lineno += 1
            try:
                pid, cmdline = line.strip().split(":", 1)
            except ValueError:
                sys.stderr.write("Warning: line %d: %s\n" % (lineno, line))
                continue
            procmap[pid] = cmdline
        procmapFile.close()

        procinfoFile = open("%s/proc.info" % datadir)
        assert procinfoFile.readline().startswith("#")
        for line in procinfoFile.readlines():
            pid, ppid, live, res, btime, elapsed = line.strip().split(",", 5)
            cur.execute("INSERT INTO proc VALUES (?,?,?,?,?,?,?)",
                (pid, ppid, live, res, btime, elapsed, procmap[pid]))
        procinfoFile.close()
    
    # trace routines
    def select_sysc(self, sysc, fields):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM syscall WHERE sysc=?" % fields, (sysc,))
        return cur.fetchall()

    def sysc_select_group_by_file(self, sysc, fields="*"):
        cur = self.cur
        cur.execute("SELECT %s FROM syscall WHERE sysc=? GROUP BY fid" 
            % fields, (sysc,))
        return cur.fetchall()
    
    def select_file(self, fid, fields):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM syscall WHERE fid=?" % fields, (fid,))
        return cur.fetchall()

    def select_sysc_on_fid(self, fid, sysc, fields="*", fetchall=True):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM syscall WHERE fid=? AND sysc=?" %
            fields, (fid, sysc))
        if fetchall: return cur.fetchall()
        else: return cur.fetchone()

    def get_first_stamp(self):
        cur = self.db.cursor()
        cur.execute("SELECT stamp FROM syscall")
        return cur.fetchone()[0]
    
    # syscall routines
    def sysc_count(self, sysc):
        cur = self.db.cursor()
        cur.execute("SELECT COUNT(*) FROM syscall WHERE sysc=?", (sysc,))
        return cur.fetchone()[0]
    
    def sysc_sum(self, sysc, field):
        cur = self.db.cursor()
        cur.execute("SELECT SUM(%s) FROM syscall WHERE sysc=?"
        "GROUP BY sysc" % field, (sysc,))
        res = cur.fetchone()
        if res is None: # No such system call
            return 0
        else:
            return res[0]
    
    def sysc_avg(self, sysc, field):
        cur = self.db.cursor()
        cur.execute("SELECT AVG(%s) FROM syscall WHERE sysc=?"
        "GROUP BY sysc" % field, (sysc,))
        res = cur.fetchone()
        if res is None: # No such system call
            return 0
        else:
            return res[0]
    
    def sysc_stddev(self, sysc, field):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM syscall WHERE sysc=?" % field, (sysc,))
        vlist = map(lambda x:x[0], cur.fetchall())
        return numpy.std(vlist)
    
    # proc map routines
    def proc_fetchall(self, fields="*"):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM proc" % fields)
        return cur.fetchall()

    def proc_select_pid(self, pid, fields):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM proc WHERE pid=?" % fields, (pid,))
        return cur.fetchall()

    def proc_get_ppid(self, pid):
        cur = self.cur
        cur.execute("SELECT ppid FROM proc WHERE pid=?", (pid,))
        return cur.fetchone()[0]
    
    # file map routines
    def file_fetchall(self, fields="*"):
        cur = self.db.cursor()
        cur.execute("SELECT %s FROM file" % fields)
        return cur.fetchall()
