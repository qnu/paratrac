#!/usr/bin/env python

#############################################################################
# ParaTrac: Scalable Tracking Tools for Parallel Applications
# Copyright (C) 2009  Nan Dun <dunnan@yl.is.s.u-tokyo.ac.jp>
#
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
# Fuse Tracker Main
#

import os
import sys

from common.version import *
from common.consts import *
from common.utils import *

from fuse.track import FUSETracker
from fuse.database import FUSETracDB

def parse_argv(argv):
    usage = "Usage: %prog [OPTIONS]"
    parser = optparse.OptionParser(usage=usage,
                 formatter=OptionParserHelpFormatter())
    
    # Tracking
    parser.add_option("-t", "--track", action="store", type="string",
        dest="track", metavar="PATH", default=None,
        help="start tracking on directory PATH")
    
    parser.add_option("-m", "--mount", action="store", type="string",
        dest="mount", metavar="PATH", default=None,
        help="mount PATH and start tracking, like \"--track\", but does not "
        "bring up monitoring interface")
    
    parser.add_option("-u", "--umount", action="store", type="string",
        dest="umount", metavar="PATH", default=None,
        help="try to unmount directory PATH")
    
    parser.add_option("--poll-rate", action="store", type="float",
        dest="pollrate", metavar="NUM", default=1.0,
        help="polling rate (default: 1)")
    
    parser.add_option("--poll-rate-multi", action="store", type="float",
        dest="pollratemulti", metavar="NUM", default=2.0,
        help="polling rate mutiplier (default: 2)")
    
    parser.add_option("--auto-umount", action="store_true",
        dest="autoumount", default=False, help="try to umount after detach")
    
    # Database
    parser.add_option("--import-log", action="store", type="string",
        dest="importlog", metavar="PATH", default=None, 
        help="import log to database")
    
    # Plot
    parser.add_option("-d", "--data", action="store", type="string",
        dest="data", metavar="PATH", default=None, 
        help="path or directory of trace data")
    
    parser.add_option("-p", "--plot", action="append", type="string",
        dest="plotlist", metavar="TYPE", default=[],
        help="plot types:\n"
             "  sysc_count: system call count\n"
             "  sysc_elapsed: elapsed time of system call\n"
             "  sysc_elapsed_sum: sum of elapsed time of system call\n"
             "  io_offset: file offset in I/O\n"
             "  io_length: request bytes in one I/O call\n"
             "  io_bytes: total bytes in I/O\n"
             "  proctree: process tree in workflow\n")
    
    parser.add_option("--ps", "--plot-series", action="append", type="string",
        dest="plotseries", metavar="SERIES", default=[],
        help="plot series")
    
    parser.add_option("--plot-log-y", action="store", type="float",
        dest="plotlogy", metavar="NUM", default=1,
        help="set y axis to log scale")

    # Debug and user interaction
    parser.add_option("-v", "--verbosity", action="store", type="choice",
        dest="verbosity", metavar="NUM", default='0', 
        choices=['0','1','2','3'],
        help="verbosity level: 0/1/2/3 (default: 0)")

    parser.add_option("--no-prompt", action="store_false",
        dest="prompt", default=True, help="user prompt (default: on)")
    
    if len(argv) == 0:
        parser.print_help()
        sys.exit(0)

    opts, args = parser.parse_args(argv)
    
    # Tracking options
    if opts.track is not None:
        opts.mountpoint = os.path.abspath(opts.track)
    if opts.mount is not None:
        opts.mountpoint = os.path.abspath(opts.mount)
    if opts.umount is not None:
        opts.mountpoint = os.path.abspath(opts.umount)
    
    opts.pollrate = 1.0 / opts.pollrate
    
    # Database options

    # Plot options
    if opts.plotlist is not None:
        # check data directory
        if opts.data is None:
            sys.stderr.write("error: data path or directory required\n")
            sys.exit(1)
        elif os.path.isdir(opts.data):
            opts.data = os.path.abspath("%s/trace.db" % opts.data)

    # Debug options
    # choice type only supports string, change verbosity back to number
    opts.verbosity = eval(opts.verbosity)

    return opts, args

def main():
    opts, args = parse_argv(sys.argv[1:])
    
    # Tracking
    if opts.mount or opts.umount or opts.track:
        tracker = FUSETracker(opts)
    if opts.mount:
        return tracker.mount()
    if opts.umount:
        return tracker.umount()
    if opts.track:
        return tracker.track()

    # Database
    if opts.importlog:
        database = FUSETracDB("%s/trace.db" % opts.importlog)
        database.create_tables()
        database.import_data()
        return 0

    # Plot
    if opts.plotlist:
        from fuse.plot import FUSETracPlot # performance
        plot = FUSETracPlot(opts.data, opts)
        plot.plot()
        plot.show()
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
