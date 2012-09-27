# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

# This is your preferences dialog.
#
# Define your preferences in
# data/glib-2.0/schemas/net.launchpad.generalcarto.gschema.xml
# See http://developer.gnome.org/gio/stable/GSettings.html for more info.

from gi.repository import Gio # pylint: disable=E0611

import gettext
from gettext import gettext as _
gettext.textdomain('generalcarto')

import logging
logger = logging.getLogger('generalcarto')

from generalcarto_lib.PreferencesDialog import PreferencesDialog

class PreferencesGeneralcartoDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesGeneralcartoDialog"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesGeneralcartoDialog, self).finish_initializing(builder)

        # Bind each preference widget to gsettings
        settings = Gio.Settings("net.launchpad.generalcarto")
        widget = self.builder.get_object('example_entry')
        settings.bind("example", widget, "text", Gio.SettingsBindFlags.DEFAULT)

        # Code for other initialization actions should be added here.

    
