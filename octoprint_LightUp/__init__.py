# coding=utf-8
from __future__ import absolute_import
import re
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
			self.__blink['Blinking'] = False
			self.__blink['Step'] = -1
			self.__running = False
			if event == Events.PRINT_STARTED:
				self._running = True
		elif event == Events.PRINT_CANCELLED:
			self.__lightLed(None, 255, 165, 0)
			self.__blink['Blinking'] = False
			self.__blink['Step'] = -1
			self.__running = False
		elif event == Events.PRINT_FAILED:
			self.__lightLed(None, 255, 0, 0)
			self.__blink['Blinking'] = False
			self.__blink['Step'] = -1
			self.__running = False
		else:
			self.__doBlink() # If we have a blinking LED, let it blink

	##~~ ProgressPlugin mixin
	def on_print_progress(self, storage, path, progress):
		if not self.__running:
			return
		# If sequential, then we use the leds as a progress bar except the ones for lighting.
		if self.__sequential:
			count = self.__ledcount - len(self.__ledLighting)
			progresscount = int(progress * count / 100)
			self.__blink['Blinking'] = False # First, we set it to false, then switch it on again, if needed.
			index = 0 # internal counter for progress bar leds.
			# i is global counter for all leds.
			for i in range(self.__ledcount):
				if i in self.__ledLighting:
					self.__lightLed(i, 255, 255, 255)
				else:
					if index == progresscount:
						self.__blink['Blinking'] = True
						self.__blink['Index'] = i
						#self._logger.info("Set Blink index {}".format(i))
						self.__doBlink()
					elif index < progresscount:
						self.__lightLed(i, 0, 0, 255)
					else:
						self.__lightLed(i, 0, 128, 0)
					index += 1

		# If not sequential, then we use a color gradient
		else:
			color = int(progress * 2.55)
			self.__lightLed(None, 0, 0, color)

	# Helper for lighting all leds (i = None) or one Leds (i is index to that led).
	# Brightness will be gamma corrected (cf. https://learn.adafruit.com/led-tricks-gamma-correction/the-quick-fix)
	def __lightLed(self, i, r, g, b):
		try:
			r = self.__gamma8[int(r)]
			g = self.__gamma8[int(g)]
			b = self.__gamma8[int(b)]
			if i is None:
				self._printer.commands("M150 R{} U{} B{}".format(r, g, b))
				#self._logger.info("M150 R{} U{} B{}".format(r, g, b))
			else:
				self._printer.commands("M150 R{} U{} B{} I{}".format(r, g, b, i))
				#self._logger.info("M150 R{} U{} B{} I{}".format(r, g, b, i))

		except:
			pass

	# Helper for clearing all leds
	def __clearLeds(self, start):
		for i in range(start, self.__ledcount):
			self.__lightLed(i, 0, 0, 0)

	# Helper for blinking the recent progress led.
	def __doBlink(self):
		try:
			if not self.__blink['Blinking']: # Blinking deactivated
				#self._logger.info("No Blinking")
				return
			# We don't want to blink the lighting leds, if they are the beginning
			while self.__blink['Index'] in self.__ledLighting:
				self.__blink['Index'] += 1
				#self._logger.info("Blink incr {}".format(self.__blink['Index']))
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

	def __parseLighting(self, lightSetting):
		if lightSetting is None:
			return None
			
		parsed = []
		parts = lightSetting.split(",")
		for part in parts:
			matches = re.findall("(\\d+)\\s*-?\\s*(\\d+)?", part.strip())
			#self._logger.info("matches {}".format(matches))
			# If there was no match or more than one matches, there is an error
			if matches is None or len(matches) != 1:
				return None
		
			# Settings indices are 1-based, led indices are 0-based
			ledstart = int(matches[0][0])-1
			ledend = None
			if len(matches[0][1]) > 0: # there was an interval
				ledend = int(matches[0][1]) # Here we don't decrement, because range is not open ended.
			
			if ledend is None:
				parsed.append(ledstart)
			else:
				parsed.extend(list(range(ledstart, ledend)))

		return parsed

## ----- Plugin infrastructure -----
	##~~ SettingsPlugin mixin
	def get_settings_defaults(self):
		return dict(
			ledcount = 10,
			sequential = True,
			ledlighting = "1,10"
		)

	def get_template_vars(self):
		return dict(
			ledcount = self._settings.get(["ledcount"]),
			sequential = self._settings.get(["sequential"]),
			ledlighting = self._settings.get(["ledLighting"])
		)

	def get_template_configs(self):
		return [
			dict(type="navbar", custom_bindings=False),
			dict(type="settings", custom_bindings=False)
		]

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

	def on_after_startup(self):
		self.__ledcount = self._settings.get(["ledcount"])
		self.__sequential = self._settings.get(["sequential"])
		self.__ledLighting = self.__parseLighting(self._settings.get(["ledLighting"]))
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
			215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255 
		)
		self.__running = False
		self._logger.info("OctoPrint-LightUp loaded!")


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
	}

