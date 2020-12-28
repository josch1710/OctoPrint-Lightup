# coding=utf-8
from __future__ import absolute_import
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
			self.__lightLed(None, 0, 255, 0)
			if event == Events.PRINT_DONE:
				self.__blink['Blinking'] = False
				self.__blink['Step'] = -1
			elif event == Events.PRINT_STARTED and self.sequential:
				self.__blink['Blinking'] = True
				self.__blink['Index'] = 0
			#self._logger.info("M150 R0 U255 B0")
		elif event == Events.PRINT_CANCELLED:
			self.__lightLed(None, 255, 165, 0)
			self.__blink['Blinking'] = False
			self.__blink['Step'] = -1
			#self._logger.info("M150 R255 U165 B0")
		elif event == Events.PRINT_FAILED:
			self.__lightLed(None, 255, 0, 0)
			self.__blink['Blinking'] = False
			self.__blink['Step'] = -1
			#self._logger.info("M150 R255 U0 B0")

		self.__doBlink() # If we have a blinking LED, let it blink

	##~~ ProgressPlugin mixin
	def on_print_progress(self, storage, path, progress):
		# If sequential, then we use the leds ####--->not now except the last two as a progress bar
		if self.sequential:
			count = self.ledcount #- 2
			progresscount = int(progress * count / 100)
			self.__blink['Blinking'] = False # First, we set it to false, then switch it on again, if needed.
			for i in range(count):
				if (i == progresscount):
					self.__blink['Blinking'] = True
					self.__blink['Index'] = i
					self.__doBlink()
				elif (i < progresscount):
					self.__lightLed(i, 0, 0, 255)
				else:
					self.__lightLed(i, 0, 0, 0)
		# If not sequential, then we use a color gradient
		else:
			color = int(progress * 2.55)
			self.__lightLed(None, 0, 0, color)

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			ledcount = 10,
			sequential = True
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
		self.ledcount = self._settings.get(["ledcount"])
		self.sequential = self._settings.get(["sequential"])
		self.__blink = {'Blinking': False, 'Step': -1, 'Index': -1 }
		self.__blinkSteps = 5
		# Table lifted from here: https://learn.adafruit.com/led-tricks-gamma-correction/the-quick-fix
		self.__gamma8 = (
			0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
			0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
			1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
			2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
			5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
			10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
			17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
			25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
			37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
			51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
			69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
			90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
			115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
			144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
			177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
			215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255 )
		self._logger.info("OctoPrint-LightUp loaded!")

	def __lightLed(self, i, r, g, b):
		try:
			r = self.__gamma8[int(r)]
			g = self.__gamma8[int(g)]
			b = self.__gamma8[int(b)]
			if i is not None:
				self._printer.commands("M150 R{} U{} B{} I{}".format(r, g, b, i))
				#self._logger.info("M150 R{} U{} B{} I{}".format(r, g, b, i))
			else:
				self._printer.commands("M150 R{} U{} B{}".format(r, g, b))
				##self._logger.info("M150 R{} U{} B{}".format(r, g, b))
		except:
			pass

	def __doBlink(self):
		try:
			if not self.__blink['Blinking']: # Blinking deactivated
				self._logger.info("No Blinking")
				return
			if self.__blinkSteps == 0:
				self.__blinkSteps = 1
			if self.__blink['Step'] < 0:
				self.__blink['Step'] = 0
			if self.__blink['Step'] >= self.__blinkSteps:
				self.__blink['Step'] = 0
			color = int(self.__blink['Step'] * 255 / self.__blinkSteps)
			self.__blink['Step'] += 1
			self.__lightLed(self.__blink['Index'], 0, 0, color)
			#self._logger.info("M150 R0 U0 B{} I{}".format(color, self.__blink['Index']))
		except AttributeError: #as data:
			#self._logger.info("Exception {}".format(data))
			pass

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Light Up"

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

