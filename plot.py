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
# To use plot.py, matplotlib is required
# see http://matplotlib.sourceforge.net for details
#

__all__ = ["Plot", "FUSETracPlot"]

import os
import sys
import numpy
import matplotlib.pyplot
import matplotlib.widgets

from common import *
from track import FUSETRAC_SYSCALL
from data import *

class Plot():
    def __init__(self, dbfile):
        self.datadir = os.path.dirname(dbfile)
        self.db = None
        self.pyplot = matplotlib.pyplot
        self.widgets = matplotlib.widgets
        
        self.usewin = False
        self.prompt = True
        
        self.ws = sys.stdout.write
        self.es = sys.stderr.write
    
    def show(self):
        if self.usewin:
            self.pyplot.show()

    def format_data_float(self, data):
        return "%.9f" % data

class FUSETracPlot(Plot):
    def __init__(self, dbfile, opts=None):
        Plot.__init__(self, dbfile)
        self.db = FUSETracDB(dbfile)
        self.plotlist = []
        self.plotseries = []
        self.plotlogy = 1

        if opts is not None:
            for k, v in opts.__dict__.items():
                if self.__dict__.has_key(k):
                    self.__dict__[k] = v

    def plot(self):
        # System call
        if "sysc_count" in self.plotlist:
            self.usewin = True
            self.plot_syscall_count()
        if "sysc_elapsed" in self.plotlist:
            self.usewin = True
            self.plot_syscall_elapsed()
        if "sysc_elapsed_sum" in self.plotlist:
            self.usewin = True
            self.plot_syscall_elapsed_sum()
        
        # I/O
        if "io_offset" in self.plotlist:
            self.usewin = True
            self.plot_io_offset()
        if "io_length" in self.plotlist:
            self.usewin = True
            self.plot_io_length()
        if "io_bytes" in self.plotlist:
            self.usewin = True
            self.plot_io_bytes()

        if "proctree" in self.plotlist:
            self.plot_proctree()
        if "workflow" in self.plotlist:
            self.plot_workflow()
    
    # Plot routines for each type of figure
    def plot_syscall_count(self):
        if self.plotseries == []:
            syscalls = FUSETRAC_SYSCALL
        else:
            syscalls = list_intersect([self.plotseries, FUSETRAC_SYSCALL])
        
        fig = self.pyplot.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_title("System Calls Counts")
        ax.set_xlabel("Time Stamp (seconds)")
        ax.set_ylabel("Operation Count")
        ax.fmt_xdata = self.format_data_float
        ax.fmt_ydata = self.format_data_float
        
        sysc_num = [SYSCALL[s] for s in syscalls]
        first_stamp = self.db.get_first_stamp()
        lines = []
        for sc in sysc_num:
            stamp = []
            count = []
            sum = 0
            for s in self.db.select_sysc(sc, "stamp"):
                sum += 1
                stamp.append(s[0] - first_stamp)
                count.append(sum)
            lines.append(ax.plot(stamp, count, linewidth=0.5, picker=5))
               
        # plot legend
        ax.legend(lines, syscalls, loc=(1.0,0.1), numpoints=1)
        legends = ax.get_legend()
        legends.draw_frame(False)
        for t in legends.get_texts():
            t.set_size("small")

    def plot_syscall_elapsed(self):
        if self.plotseries == []:
            syscalls = FUSETRAC_SYSCALL
        else:
            syscalls = list_intersect([self.plotseries, FUSETRAC_SYSCALL])
        
        fig = self.pyplot.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_title("System Calls Elapsed Time")
        ax.set_xlabel("Time Stamp (seconds)")
        ax.set_ylabel("Elapsed Time (seconds)")
        ax.fmt_xdata = self.format_data_float
        ax.fmt_ydata = self.format_data_float

        if self.plotlogy != 1:
            ax.semilogy(basex=self.plotlogy)

        sysc_num = [SYSCALL_FILESYSTEM[s] for s in syscalls]
        first_stamp = self.db.get_first_stamp()
        lines = []
        for sc in sysc_num:
            stamp = []
            elapsed = []
            for s,e in self.db.select_sysc(sc, "stamp,elapsed"):
                stamp.append(s - first_stamp)
                elapsed.append(e)
            lines.append(ax.plot(stamp, elapsed, linewidth=0.3))
        
        # plot legend
        ax.legend(lines, syscalls, loc=(1.0,0.1), numpoints=1)
        legends = ax.get_legend()
        legends.draw_frame(False)
        for t in legends.get_texts():
            t.set_size("small")

    def plot_syscall_elapsed_sum(self):
        if self.plotseries == []:
            syscalls = FUSETRAC_SYSCALL
        else:
            syscalls = list_intersect([self.plotseries, FUSETRAC_SYSCALL])
        
        fig = self.pyplot.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_title("Summation of System Calls Elapsed Time")
        ax.set_xlabel("Time Stamp (seconds)")
        ax.set_ylabel("Summation of Elapsed Time (seconds)")
        ax.fmt_xdata = self.format_data_float
        ax.fmt_ydata = self.format_data_float

        if self.plotlogy != 1:
            ax.semilogy(basex=self.plotlogy)
        
        sysc_num = [SYSCALL_FILESYSTEM[s] for s in syscalls]
        first_stamp = self.db.get_first_stamp()
        lines = []
        for sc in sysc_num:
            stamp = []
            esum = []
            sum = 0
            for s,e in self.db.select_sysc(sc, "stamp,elapsed"):
                sum += e
                stamp.append(s - first_stamp)
                esum.append(sum)
            lines.append(ax.plot(stamp, esum, linewidth=1))
        
        # plot legend
        ax.legend(lines, syscalls, loc=(1.0,0.1), numpoints=1)
        legends = ax.get_legend()
        legends.draw_frame(False)
        for t in legends.get_texts():
            t.set_size("small")
    
    def plot_io_offset(self):
        if self.plotseries == []:
            syscalls = ["read", "write"]
        else:
            syscalls = list_intersect([self.plotseries, ["read", "write"]])
        
        fig = self.pyplot.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_title("File Offset in I/O")
        ax.set_xlabel("Time Stamp (seconds)")
        ax.set_ylabel("Requested Offset (bytes)")
        ax.fmt_xdata = self.format_data_float
        ax.fmt_ydata = self.format_data_float
        
        if self.plotlogy != 1:
            ax.semilogy(basex=self.plotlogy)
        # db format
        # stamp, pid, sysc, fid, res, elapsed, size, offset
        sysc_num = [SYSCALL_FILESYSTEM[s] for s in syscalls]
        first_stamp = self.db.get_first_stamp()
        lines = []
        for sc in sysc_num:
            stamp = []
            offset = []
            for s,o in self.db.select_sysc(sc, "stamp,aux2"):
                stamp.append(s - first_stamp)
                offset.append(o)
            lines.append(ax.plot(stamp, offset, linewidth=0.3))
        
        # plot legend
        ax.legend(lines, syscalls, loc=(1.0,0.1), numpoints=1)
        legends = ax.get_legend()
        legends.draw_frame(False)
        for t in legends.get_texts():
            t.set_size("small")
        
    def plot_io_length(self):
        if self.plotseries == []:
            syscalls = ["read", "write"]
        else:
            syscalls = list_intersect([self.plotseries, ["read", "write"]])
        
        fig = self.pyplot.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_title("I/O Length")
        ax.set_xlabel("Time Stamp (seconds)")
        ax.set_ylabel("Requested Length (bytes)")
        ax.fmt_xdata = self.format_data_float
        ax.fmt_ydata = self.format_data_float
        
        if self.plotlogy != 1:
            ax.semilogy(basex=self.plotlogy)
        # db format
        # stamp, pid, sysc, fid, res, elapsed, size, offset
        sysc_num = [SYSCALL_FILESYSTEM[s] for s in syscalls]
        first_stamp = self.db.get_first_stamp()
        lines = []
        for sc in sysc_num:
            stamp = []
            length = []
            for s,l in self.db.select_sysc(sc, "stamp,aux1"):
                stamp.append(s - first_stamp)
                length.append(l)
            lines.append(ax.plot(stamp, length, linewidth=0.3))
        
        # plot legend
        ax.legend(lines, syscalls, loc=(1.0,0.1), numpoints=1)
        legends = ax.get_legend()
        legends.draw_frame(False)
        for t in legends.get_texts():
            t.set_size("small")
    
    def plot_io_bytes(self):
        if self.plotseries == []:
            syscalls = ["read", "write"]
        else:
            syscalls = list_intersect([self.plotseries, ["read", "write"]])
        
        fig = self.pyplot.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_title("Total I/O Bytes")
        ax.set_xlabel("Time Stamp (seconds)")
        ax.set_ylabel("Data Volumn (bytes)")
        ax.fmt_xdata = self.format_data_float
        ax.fmt_ydata = self.format_data_float
        
        if self.plotlogy != 1:
            ax.semilogy(basex=self.plotlogy)
        # db format
        # stamp, pid, sysc, fid, res, elapsed, size, offset
        sysc_num = [SYSCALL_FILESYSTEM[s] for s in syscalls]
        first_stamp = self.db.get_first_stamp()
        lines = []
        for sc in sysc_num:
            stamp = []
            bytes = []
            sum = 0
            for s,l in self.db.select_sysc(sc, "stamp,aux1"):
                sum += l 
                stamp.append(s - first_stamp)
                bytes.append(sum)
            lines.append(ax.plot(stamp, bytes, linewidth=0.3))
        
        # plot legend
        ax.legend(lines, syscalls, loc=(1.0,0.1), numpoints=1)
        legends = ax.get_legend()
        legends.draw_frame(False)
        for t in legends.get_texts():
            t.set_size("small")

    # workflow plot using Graphviz
    def plot_proctree(self):
        gvFile = open("%s/proctree.gv" % self.datadir, "wb")
        sifFile = open("%s/proctree.sif" % self.datadir, "wb")
        noaFile = open("%s/proctree.noa" % self.datadir, "wb")
        
        gvFile.write("digraph proctree {\n")
        for pid, ppid, cmdline in self.db.procmap_fetchall():
            gvFile.write("\t%d->%d;\n" % (ppid, pid))
            sifFile.write("%d call %d\n" % (ppid, pid))
            noaFile.write("%d = %s\n" % (pid, cmdline))
        gvFile.write("}\n")
        
        gvFile.close()
        sifFile.close()
        noaFile.close()
        
        # prompt user
        if self.prompt:
            self.ws("Process tree graph has been created.\n"
                    "Please use Graphviz to visualize:\n"
                    "  %s/proctree.gv\n"
                    "Please use Cytoscape to visualize:\n"
                    "  %s/proctree.sif\n"
                    "  %s/proctree.noa\n"
                    % (self.datadir, self.datadir, self.datadir))

    def plot_workflow(self):
        NEW = [SYSCALL[i] for i in ["mknod", "mkdir", "creat"]]
        DEL = [SYSCALL[i] for i in ["unlink", "rmdir"]]
        IN = [SYSCALL["read"]]
        OUT = [SYSCALL["write"]]
        TRAN = [SYSCALL[i] for i in ["symlink", "rename", "link"]]
        sifFile = open("%s/workflow.sif" % self.datadir, "wb")
        ncsvFile = open("%s/workflow-nodes.csv" % self.datadir, "wb")
        ecsvFile = open("%s/workflow-edges.csv" % self.datadir, "wb")

        ncsvFile.write("id,type,info\n")
        ecsvFile.write("id,bytes\n")
        
        pids = []
        for sysc in NEW:
            log = self.db.select_sysc(sysc, "pid,fid")
            if log is not None:
                for pid, fid in log:
                    sifFile.write("p%d %s f%d\n" % (pid, SYSCALL[sysc], fid))
                    pids.append(pid)

        for sysc in DEL:
            log = self.db.select_sysc(sysc, "pid,fid")
            if log is not None:
                syscname = SYSCALL[sysc]
                for pid, fid in log:
                    sifFile.write("f%d %s p%d\n" % (fid, syscname, pid))
                    pids.append(pid)

        for sysc in TRAN:
            log = self.db.select_sysc(sysc, "pid,fid,aux1")
            if log is not None:
                syscname = SYSCALL[sysc]
                for pid, fromfid, tofid in log:
                    sifFile.write("f%d %s p%d\n" % (fromfid, syscname, pid))
                    sifFile.write("p%d %s f%d\n" % (pid, syscname, tofid))
                    pids.append(pid)

        for sysc in IN:
            log = self.db.select_sysc_group_by_file(sysc, "pid,fid,SUM(aux1)")
            if log is not None:
                syscname = SYSCALL[sysc]
                for pid, fid, bytes in log:
                    sifFile.write("f%d %s p%d\n" % (fid, syscname, pid))
                    ecsvFile.write("f%d (%s) p%d,%d\n" 
                        % (fid, syscname, pid, bytes))
                    pids.append(pid)
        
        for sysc in OUT:
            log = self.db.select_sysc_group_by_file(sysc, "pid,fid,SUM(aux1)")
            if log is not None:
                syscname = SYSCALL[sysc]
                for pid, fid, bytes in log:
                    sifFile.write("p%d %s f%d\n" % (pid, syscname, fid))
                    ecsvFile.write("p%d (%s) f%d,%d\n" 
                        % (pid, syscname, fid, bytes))
                    pids.append(pid)
        
        for pid in pids:
            ppid = self.db.procmap_get_ppid(pid)
            sifFile.write("p%d fork p%d\n" % (ppid, pid))

        # output node attributes
        for item in self.db.procmap_fetchall("pid,cmdline"):
            ncsvFile.write("p%d,proc,%s\n" % item)
        for item in self.db.filemap_fetchall():
            ncsvFile.write("f%d,file,%s\n" % item)

        sifFile.close()
        ncsvFile.close()
        ecsvFile.close()
        
        # prompt user
        if self.prompt:
            self.ws("Workflow DAG has been created.\n"
                    "Please use Cytoscape to visualize following data:\n"
                    "  %s/workflow.sif\n"
                    "  %s/workflow-nodes.csv\n"
                    "  %s/workflow-edges.csv\n"
                    % (self.datadir, self.datadir, self.datadir))