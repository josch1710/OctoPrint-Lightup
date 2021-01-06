/*
 * View model for OctoPrint-Lightup
 *
 * Author: Jochen Schäfer
 * License: AGPLv3
 */
$(function() {
    function LightupViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        self.sequential = ko.observable();
        self.ledcount = ko.observable();
        self.ledlighting = ko.observable();

        self.sequential.subscribe(function(value)
        {
            console.debug("sequential", value);
        });

        self.onBeforeBinding = function()
        {
            self.mySettings = self.settingsViewModel.settings.plugins.LightUp;
            self.sequential(self.mySettings.value);
            self.ledcount(self.mySettings.value);
            self.ledlighting(self.mySettings.value);
        };

        self.onConfigClose = function()
        {
            var data = {
                plugins: {
                    LightUp: {
                        sequential: self.sequential(),
                        ledcount: self.ledcount(),
                        ledlighting: self.ledlighting()
                    }
                }
            };
            self.settingsViewModel.saveData(data);
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: LightupViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ /* "loginStateViewModel",*/ "settingsViewModel" ],
        // Elements to bind to, e.g. #settings_plugin_LightUp, #tab_plugin_LightUp, ...
        elements: [ /*"#settings_plugin_LightUp"*/ ]
    });
});
