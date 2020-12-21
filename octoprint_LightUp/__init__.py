# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
from octoprint.events import Events

class LightupPlugin(octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.TemplatePlugin,
					octoprint.plugin.ProgressPlugin,
					octoprint.plugin.EventHandlerPlugin,
					octoprint.plugin.StartupPlugin):

	##~~ EventHandlerPlugin mixin
	def on_event(self, event, payload):
		if event in (Events.PRINT_DONE, Events.PRINT_STARTED):
			self._printer.commands("M150 R0 U255 B0")
			#self._logger.info("M150 R0 U255 B0")
		elif event == Events.PRINT_CANCELLED:
			self._printer.commands("M150 R255 U165 B0")
			#self._logger.info("M150 R255 U165 B0")
		else:
			self._printer.commands("M150 R255 U0 B0")
			#self._logger.info("M150 R255 U0 B0")

	##~~ ProgressPlugin mixin
	def on_print_progress(self, storage, path, progress):
		# If sequential, then we use the leds ####--->not now except the last two as a progress bar
		if self.sequential:
			count = self.ledcount #- 2
			progresscount = int(progress * count / 100)
			for i in range(count):
				if (i == progresscount):
					if self.blinking is None:
						self.blinking = True
					if self.blinking:
						self._printer.commands("M150 R255 U255 B0 I{}".format(i))
					else:
						self._printer.commands("M150 R100 U100 B0 I{}".format(i))
					self._logger.info("Blinking {} -> {}, {}".format(progress, progresscount, i))	
					self.blinking = not self.blinking
				elif (i < progresscount):
					self._printer.commands("M150 R255 U255 B0 I{}".format(i))
			    	#self._logger.info("M150 R255 U255 B0 I{}".format(i))
				else:
					self._printer.commands("M150 R0 U0 B0 I{}".format(i))
					#self._logger.info("M150 R0 U0 B0 I{}".format(i))
		# If not sequential, then we use a color gradient
		else:
			color = int(progress * 2.55)
			self._printer.commands("M150 R{} U{} B0".format(color, color))	
			#self._logger.info("M150 R{} U{} B0".format(color, color))	

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			# put your plugin's default settings here
		)

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/LightUp.js"],
			css=["css/LightUp.css"],
			less=["less/LightUp.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
		# for details.
		return dict(
			LightUp=dict(
				displayName="Lightup Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="josch1710",
				repo="OctoPrint-Lightup",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/josch1710/OctoPrint-Lightup/archive/{target_version}.zip"
			)
		)

	##~~ Temperatur 
	def get_temperature_reading(self, comm, parsed_temps):
		bed = None
		hotend = None
		for k, v in parsed_temps.items():
			self._logger.info(k)
			self._logger.info(v)
			if k == 'B':
				bed = v
			elif k == 'T0':
				hotend = v

		if self.sequential:
			if bed is not None and bed[1] is not None and bed[1] > 0:
				led_no = self.ledcount - 1
				percentage = int(bed[0] * 2.55 / bed[1])
				self._printer.commands("M150 I{} R{} U{} B0".format(led_no, percentage, percentage))
				#self._logger.info("M150 I{} R{} U{} B0".format(led_no, percentage, percentage))

			if hotend is not None and hotend[1] is not None and hotend[1] > 0:
				led_no = self.ledcount - 2
				percentage = int(hotend[0] * 2.55 / hotend[1])
				self._printer.commands("M150 I{} R{} U{} B0".format(led_no, percentage, percentage))
				#self._logger.info("M150 I{} R{} U{} B0".format(led_no, percentage, percentage))
			
		else:
			if bed is not None and bed[1] is not None and bed[1] > 0:
				percentage = int(bed[0] * 2.55 / bed[1])
				self._printer.commands("M150 R{} U{} B0".format(percentage, percentage))
				#self._logger.info("M150 R{} U{} B0".format(percentage, percentage))
			elif hotend is not None and hotend[1] is not None and hotend[1] > 0:
				percentage = int(hotend[0] * 2.55 / hotend[1])
				self._printer.commands("M150 R{} U0 B{}".format(percentage, percentage))
				#self._logger.info("M150 I{} R{} U0 B{}".format(percentage, percentage))

		return parsed_temps

	def on_after_startup(self):
		self.ledcount = 10
		self.sequential = True
		self.blinking = False

		self._logger.info("OctoPrint-LightUp loaded!")


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Lightup Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LightupPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		#"octoprint.comm.protocol.temperatures.received": __plugin_implementation__.get_temperature_reading
	}

