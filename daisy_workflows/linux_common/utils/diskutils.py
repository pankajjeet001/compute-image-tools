#!/usr/bin/env python2
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Disk utility functions for all VM scripts."""

import logging

from common import AptGetInstall
try:
  import guestfs
except ImportError:
  AptGetInstall(['python-guestfs'])
  import guestfs


def MountDisk(disk):
  # All new Python code should pass python_return_dict=True
  # to the constructor.  It indicates that your program wants
  # to receive Python dicts for methods in the API that return
  # hashtables.
  g = guestfs.GuestFS(python_return_dict=True)
  # Set the product name as cloud-init checks it to confirm this is a VM in GCE
  g.config('-smbios', 'type=1,product=Google Compute Engine')
  g.set_verbose(1)
  g.set_trace(1)

  g.set_memsize(4096)

  # Enable network
  g.set_network(True)

  # Attach the disk image to libguestfs.
  g.add_drive_opts(disk)

  # Run the libguestfs back-end.
  g.launch()

  # Ask libguestfs to inspect for operating systems.
  roots = g.inspect_os()
  if len(roots) == 0:
    raise Exception('inspect_vm: no operating systems found')

  # Sort keys by length, shortest first, so that we end up
  # mounting the filesystems in the correct order.
  mps = g.inspect_get_mountpoints(roots[0])

  def compare(a, b):
    return len(a) - len(b)

  for device in sorted(mps.keys(), compare):
    try:
      g.mount(mps[device], device)
    except RuntimeError as msg:
      logging.warn('%s (ignored)' % msg)

  return g


def UnmountDisk(g):
  try:
    g.umount_all()
  except Exception as e:
    logging.debug(str(e))
    logging.warn('Unmount failed. Continuing anyway.')
