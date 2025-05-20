# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Daz Tools",
    "author": "Dilly",
    "version": (1, 0),
    "blender": (4, 1, 0),
    "location": "UI > Daz Tools",
    "description": "Dilly's Daz tools",
    "category": "Import-Export",
}

#----------------------------------------------------------
#   Modules
#----------------------------------------------------------

Modules = ["panel", "utils"]

import bpy

#----------------------------------------------------------
#   Register
#----------------------------------------------------------

Regnames = ["panel", "utils"]

def register():
    print("Register DAZ Tools")
    for modname in Modules:
        exec("from . import %s" % modname)
    for modname in Modules:
        if modname in Regnames:
            exec("%s.register()" % modname)


def unregister():
    for modname in Modules:
        exec("from . import %s" % modname)
    for modname in reversed(Modules):
        if modname in Regnames:
            exec("%s.unregister()" % modname)

if __name__ == "__main__":
    register()
