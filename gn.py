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

"""
Oxide checkouts don't contain a GN binary like Chromium checkouts do - instead,
we provide a binary in oxide-tools and use this script to pick the right one.
However, we fall back to the depot_tools GN helper if we're not in an Oxide
checkout so that it's ok to have this on your PATH if you're working on
Chromium.

We don't rely on the GN binary provided with Chromium checkouts because they
only provide an x64 build for Linux
"""

from __future__ import print_function
import os
import os.path
import platform
import subprocess
import sys

GN_EXE = "gn"

def MaybeInChromiumCheckout():
  d = os.getcwd()
  while not os.path.isfile(os.path.join(d, ".gclient")):
    p = os.path.dirname(d)
    if p == d:
      return False
    d = p

  if os.path.isdir(os.path.join(d, "src", "oxide")):
    return False

  return True

def GetOxideGNExePath():
  platform_dir = None

  if platform.system() == "Linux":
    if platform.machine() == "x86_64":
      platform_dir = "linux64"

  if not platform_dir:
    raise Exception(
"""No pre-compiled GN binary for this platform. You will need to bootstrap
one yourself""")

  return os.path.join(os.path.dirname(__file__), platform_dir, GN_EXE)

def GetDepotToolsGNHelperPath():
  for path in os.getenv("PATH", "").split(":"):
    if (os.access(os.path.join(path, GN_EXE), os.X_OK) and
        os.path.isdir(os.path.join(path, ".git")) and
        path != os.path.dirname(__file__)):
      return os.path.join(path, GN_EXE)
  raise Exception("No depot_tools checkout found. Is it in your PATH?")

def GetGNExePath():
  if MaybeInChromiumCheckout():
    return GetDepotToolsGNHelperPath()

  return GetOxideGNExePath()

def main(argv):
  gn_path = GetGNExePath()
  assert os.access(gn_path, os.X_OK)

  args = [gn_path]
  args.extend(argv)

  return subprocess.call(args)

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
