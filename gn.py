# Copyright (C) 2016 Canonical Ltd.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from __future__ import print_function
import os
import os.path
import platform
from subprocess import CalledProcessError, check_call
import sys

def main(argv):
  gn_exe = None
  if platform.system() == "Linux":
    if platform.machine() == "x86_64":
      gn_exe = "gn.linux64"

  if not gn_exe:
    print("*** Cannot run gn - no binary available for platform \"%s/%s\" ***" %
          (platform.system(), platform.machine()), file=sys.stderr)
    print("You will need to bootstrap your own gn binary", file=sys.stderr)
    sys.exit(1)

  gn_path = os.path.join(os.path.dirname(__file__), gn_exe)

  assert os.access(gn_path, os.X_OK)

  args = [gn_path]
  args.extend(argv)

  try:
    check_call(args)
  except CalledProcessError:
    pass

if __name__ == "__main__":
  main(sys.argv[1:])
