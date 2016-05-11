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
from optparse import OptionParser
import os
import os.path
from subprocess import Popen, CalledProcessError, PIPE
import sys

def CheckCall(args, cwd=None, quiet=False):
  with open(os.devnull, "w") as devnull:
    p = Popen(args, cwd=cwd,
              stdout = devnull if quiet == True else None,
              stderr = devnull if quiet == True else None)
    r = p.wait()
    if r is not 0: raise CalledProcessError(r, args)

def CheckOutput(args, cwd=None):
  e = os.environ
  e['LANG'] = 'C'
  p = Popen(args, cwd=cwd, stdout=PIPE, env=e)
  r = p.wait()
  if r is not 0: raise CalledProcessError(r, args)
  return p.stdout.read()

def IsDepotToolsInPath():
  paths = os.environ["PATH"]
  if not paths:
    paths = "/usr/bin:/bin"
  for p in paths.split(":"):
    if os.access(os.path.join(p, "gclient"), os.X_OK):
      return True
  return False

def GclientSupportsCacheMode():
  try:
    return CheckOutput(["gclient", "supports-cache-mode"]).strip() == "Yes"
  except:
    return False

def GetGitMirrorPath(cachedir, url):
  return CheckOutput(["git", "cache", "exists",
                      "--cache-dir", cachedir, url]).strip()

def PopulateGitMirror(cachedir, url):
  CheckCall(["git", "cache", "populate", "--cache-dir", cachedir, url])
  return GetGitMirrorPath(cachedir, url)

def GetDefaultUrl(user_id):
  if user_id:
    return "git+ssh://%s@git.launchpad.net/~oxide-developers/oxide/+git/oxide" % user_id

  return "git://git.launchpad.net/~oxide-developers/oxide/+git/oxide"

class Options(OptionParser):
  def __init__(self):
    OptionParser.__init__(self, usage="%prog [options] [destination]")

    self.add_option("-b", "--branch", help="The name of the branch to check out",
                    default="master")
    self.add_option("-c", "--cache-dir",
                    help="Specify a local mirror to clone from")
    self.add_option("--cache-mode", default="reference",
                    help="The cache mode (when used with --cache-dir)."
                         "\"reference\" causes checkouts to be cloned with "
                         "--reference pointing to the local mirror, but their "
                         "origin pointing to the remote branch. \"full\" causes "
                         "checkouts to be cloned from the local mirror with "
                         "--shared")
    self.add_option("-u", "--url", help="Override the canonical source URL")
    self.add_option("--user-id", help="Your Launchpad user ID - use this to "
                                      "fetch a read/write checkout (committers "
                                      "only)")

def main():
  o = Options()
  (opts, args) = o.parse_args()

  cache_dir = opts.cache_dir
  if cache_dir:
    cache_dir = os.path.abspath(cache_dir)

  dest = os.getcwd()

  if len(args) == 1:
    dest = os.path.abspath(args[0])
  elif len(args) > 1:
    print("Invalid number of arguments", file=sys.stderr)
    o.print_usage(file=sys.stderr)
    sys.exit(1)

  if opts.cache_mode not in ("full", "reference"):
    print("Invalid value for --cache-mode", file=sys.stderr)
    o.print_usage(file=sys.stderr)
    sys.exit(1)

  if not IsDepotToolsInPath():
    print("Please check out depot_tools and ensure that it appears in your "
          "PATH environment variable.", file=sys.stderr)
    print("depot_tools can be checked out from "
          "git://git.launchpad.net/~oxide-developers/oxide/+git/depot_tools",
          file=sys.stderr)
    sys.exit(1)

  cache_mode = opts.cache_mode
  cache_mode_supported = GclientSupportsCacheMode()
  if not cache_mode_supported and cache_mode == "reference":
    print("WARNING: You are using a version of depot_tools that doesn't "
          "support cache_mode. Falling back to to --cache-mode=full. "
          "Did you check out depot_tools from "
          "git://git.launchpad.net/~oxide-developers/oxide/+git/depot_tools ?",
          file=sys.stderr)
    cache_mode = "full"

  if not os.path.exists(dest):
    os.makedirs(dest)

  if not os.path.isdir(dest):
    print("Destination exists and is not a directory", file=sys.stderr)
    sys.exit(1)

  if len(os.listdir(dest)) > 0:
    print("Destination directory exists and is not empty", file=sys.stderr)
    sys.exit(1) 

  clone_args = ["git", "clone"]
  remote_url = opts.url

  using_default_url = False
  if not remote_url:
    using_default_url = True
    remote_url = GetDefaultUrl(opts.user_id)

  clone_url = remote_url
  if cache_dir:
    if cache_mode == "full":
      clone_url = PopulateGitMirror(cache_dir, remote_url)
      clone_args.append("--shared")
    else:
      clone_args.extend(["--reference", GetGitMirrorPath(cache_dir, remote_url)])

  oxide_dest = os.path.join(dest, "src", "oxide")
  os.makedirs(os.path.dirname(oxide_dest))

  clone_args.extend([clone_url, oxide_dest])
  CheckCall(clone_args)

  CheckCall(["git", "checkout", opts.branch], cwd=oxide_dest)

  if cache_dir:
    CheckCall(["git", "config", "oxide.cacheDir", cache_dir], oxide_dest)
    CheckCall(["git", "config", "oxide.cacheMode", cache_mode], oxide_dest)
    if opts.user_id and using_default_url and cache_mode == "full":
      CheckCall(["git", "remote", "set-url", "--push", "origin", remote_url],
                oxide_dest)

  CheckCall([sys.executable,
             os.path.join(oxide_dest, "tools", "update-checkout.py")],
            cwd=oxide_dest)

  CheckCall(["git", "submodule", "foreach",
             "git config -f $toplevel/.git/config submodule.$name.ignore all"],
            os.path.join(dest, "src"))
  CheckCall(["git", "config", "diff.ignoreSubmodules", "all"],
            os.path.join(dest, "src"))

if __name__ == "__main__":
  main()
