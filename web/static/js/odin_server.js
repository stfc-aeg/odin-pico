api_version = '0.1';

// Initialize the focusFlags object with all keys set to false (not focused)
var focusFlags = {
  "bit-mode-dropdown": false,
  "time-base-input": false,
  "channel-a-active": false,
  "channel-b-active": false,
  "channel-c-active": false,
  "channel-d-active": false,
  "channel-a-coupl": false,
  "channel-b-coupl": false,
  "channel-c-coupl": false,
  "channel-d-coupl": false,
  "channel-a-range": false,
  "channel-b-range": false,
  "channel-c-range": false,
  "channel-d-range": false,
  "channel-a-offset": false,
  "channel-b-offset": false,
  "channel-c-offset": false,
  "channel-d-offset": false,
  "channel-a-liveview": false,
  "channel-b-liveview": false,
  "channel-c-liveview": false,
  "channel-d-liveview": false,
  "channel-a-pha": false,
  "channel-b-pha": false,
  "channel-c-pha": false,
  "channel-d-pha": false,
  "trigger-enable": false,
  "trigger-source": false,
  "trigger-direction": false,
  "trigger-threshold": false,
  "trigger-delay": false,
  "trigger-auto": false,
  "capture-pretrig-samples": false,
  "capture-posttrig-samples": false,
  "capture-count": false,
  "capture-folder-name": false,
  "capture-file-name": false,
  "pha-num-bins": false,
  "pha-lower-range": false,
  "pha-upper-range": false,
  "capture-time": false,
  "capture-mode-num": true,
  "capture-mode-time": false,
  "repeat-amount": false,
  "cap-repeat": false,
  "delay-time": false,
  "gpib-enable": false,
  "sweep-active": false,
  "sweep-start": false,
  "sweep-end": false,
  "sweep-step": false,
  "sweep-tol": false,
  "gpib-device-select": false
};

// Initialize a timers object to keep track of the timers for each field
var timers = {};

// Time limit (in milliseconds) after which to blur the input
var timeLimit = 10000; // 5 seconds

// Initialise arrays to be used
var pha_array = []
var lv_data = []
var active_channels_lv = []

// Initialise variables for pausing the LV/PHA graphs
play_button_lv = true;
play_button_pha = true;

// Run when the script is loaded
$( document ).ready(function() {
    update_api_version();
    run_sync();
});

// Get the most up to date api version
function update_api_version() {
    $.getJSON('/api', function(response) {
        $('#api-version').html(response.api);
        api_version = response.api;
    });
}
// Resize plotly graphs after window changes size
function resize_plotly() {
    let div_width = 0.9*(document.getElementById('setup-6')).offsetWidth;

    let update = {
        width: div_width,  // Set the width to the container div's width
        height: 300
    };
  
    Plotly.relayout('scope_lv', update);
    Plotly.relayout('scope_pha', update);
}

// Listener event for resizing 
window.addEventListener('resize', resize_plotly);

window.addEventListener('resize', function() {
    location.reload();
  });

// Initialize the focus and blur events
Object.keys(focusFlags).forEach(function(key) {
    $("#" + key).focus(function() {
      focusFlags[key] = true;
      
      // Clear any existing timer for this input
      clearTimeout(timers[key]);
      
      // Set a new timer for this input
      timers[key] = setTimeout(function() {
        // Blur the input if the timer runs out
        $("#" + key).blur();
      }, timeLimit);
    });
    
    $("#" + key).blur(function() {
      focusFlags[key] = false;
      
      // Clear the timer when the input loses focus
      clearTimeout(timers[key]);
    });
    
    $("#" + key).change(function() {
      // Clear the timer when the input changes, so it doesn't blur
      clearTimeout(timers[key]);
      
      // Optionally, reset the timer
      timers[key] = setTimeout(function() {
        $("#" + key).blur();
      }, timeLimit);
    });
  });

function toggle_play_lv() {
    const button_lv = document.getElementById('p_p_button_lv');
    play_button_lv = !play_button_lv;
    
    // Change the icon depending on whether the graph is active or inactive
    if (play_button_lv) {
      button_lv.innerHTML = '<span class="material-icons">pause_circle_outline</span>'; 
    } else {
      button_lv.innerHTML = '<span class="material-icons">play_circle_outline</span>';
    }
  }

function toggle_play_pha() {
    const button_pha = document.getElementById('p_p_button_pha');
    play_button_pha = !play_button_pha;

    // Change the icon depending on whether the graph is active or inactive
    if (play_button_pha) {
        button_pha.innerHTML = '<span class="material-icons">pause_circle_outline</span>';
    } else {
        button_pha.innerHTML = '<span class="material-icons">play_circle_outline</span>';
    }
}

function update_pha_graph() {

    if (play_button_pha) {

        pha_data = []

        scope_pha = document.getElementById('scope_pha');

        num_data = 0

        // Identify the data to be displayed on the graph
        for (var chan = 0; chan < 4; chan++) {
            if (pha_channels[chan] == true) {
                pha_data.push({
                    x: x = bin_edges,
                    y: y = pha_array[chan],
                    name: ('Channel ' + String.fromCharCode(chan+65)),
                    type: 'scatter',
                    line: {color: channel_colours[chan]}
                })
            }
        }

        // Identify the layout to be used for the graph
        layout = {
            title: 'Current PHA Data',
            margin: { t: 50, b: 60 },
            xaxis: {
                title: 'Energy Level (ADC_Counts)',
                range: [lower_range, upper_range],
            },
            yaxis: {title: 'Counts'},
            autosize: true,
            showlegend: true,
        }

        // Create the graph
        Plotly.newPlot((document.getElementById('scope_pha')), pha_data, layout, {scrollZoom: true})
    }
}

function update_lv_graph() {

    if (play_button_lv) {

        var tickText = []
        var tickVals = []

        var pre_samples = document.getElementById("capture-pretrig-samples").value
        var post_samples = document.getElementById("capture-posttrig-samples").value

        // Use smallest range if no channels active
        if (active_channels_lv.length > 0) {
            let range = get_range_value_mv(active_channels_lv[0])
        }
            let range = get_range_value_mv(0)

        lv_data = []

        // Create the values to be seen on the graph axes
        for (var i = -range; i <= range; i += (range / 4)) {
            tickVals.push(i);
            tickText.push(i.toFixed(1)); 
        }

        // Create a basic layout, designed for an empty graph with no data
        layout = {
            title: 'Live View of PicoScope Traces',
            margin: { t: 50, b: 60 },
            xaxis: {
                title: 'Sample Interval',
                range: [-pre_samples, post_samples],
            },
            yaxis: {
                title: ('Channel  Voltage (mV)'),
                range: [-range, range],
                ticktext: tickText,
                tickvals: tickVals,
            },
            autosize: true,
            showlegend: true,
            legend: {
                orientation: 'h'
            }
        }

        var pre_samples = document.getElementById("capture-pretrig-samples").value

        // Prepare the data to be shown on the graph
        for (var chan = 0; chan < active_channels_lv.length; chan++) {
            lv_data.push ({
                x: x = data_array[chan].map((value, index)=> (index - pre_samples)),
                y: y = data_array[chan],
                name: ('Channel '+ active_channels_lv_letters[chan]),
                type: 'scatter',
                line: {color: channel_colours[active_channels_lv[chan]]},
            })
            // Check if a channel is active, change axis labels and assign data
            if (chan == 0) {
                let range = get_range_value_mv(chan_ranges[active_channels_lv[0]])


                tickText = []
                tickVals = []
                for (var i = -range; i <= range; i += (range / 4)) {
                    tickVals.push(i);
                    tickText.push(i.toFixed(1)); 
                }
       
                lv_data[chan].yaxis = 'y1'

                layout.yaxis = {
                    title: ('Channel ' + active_channels_lv_letters[chan] + ' Voltage (mV)'),
                    range: [-range, range],
                    ticktext: tickText,
                    tickvals: tickVals,
                }
            
            // Check if a second channel is active, change axis labels and assign data
            } else if (chan == 1) {
                let range2 = get_range_value_mv(chan_ranges[active_channels_lv[1]])

                tickText2 = []
                tickVals2 = []

                for (var i = -range2; i <= range2; i += (range2 / 4)) {
                    tickVals2.push(i);
                    tickText2.push(i.toFixed(1)); 
                }

                lv_data[chan].yaxis = 'y2'
                layout.yaxis2 = {
                    title: ('Channel ' + active_channels_lv_letters[chan] + ' Voltage (mV)'),
                    side: 'right',
                    overlaying: 'y',
                    range: [-range2, range2],
                    ticktext: tickText2,
                    tickvals: tickVals2
                }
            }

        }

        // Create the graph
        Plotly.newPlot((document.getElementById('scope_lv')), lv_data, layout, {scrollZoom: true})
    }
}

function run_sync(){
    $.getJSON('/api/' + api_version + '/pico/', sync_with_adapter());
    setTimeout(run_sync, 150);
}

function get_range_value_mv(key) {
    // Compare the range key to the actual range
    var range_values = {
        0: 10,
        1: 20,
        2: 50,
        3: 100,
        4: 200,
        5: 500,
        6: 1000,
        7: 2000,
        8: 5000,
        9: 10000,
        10: 20000
    };

    if (key in range_values) {
        return range_values[key];
    }
}

function sync_with_adapter(){

    return function(response){

        const tab  = document.getElementById("gpib-tab");
        const pane = document.getElementById("three");

        if (response.gpib && response.gpib.gpib_avail === true) {

            // reveal the tab
            tab.style.display = "block";

            // master toggle
            if (!focusFlags["gpib-enable"]) {
                document.getElementById("gpib-enable").checked =
                    Boolean(response.gpib.gpib_control);
            }

            // device selector 
            const devSel = document.getElementById("gpib-device-select");
            if (devSel) {
                const devs   = response.gpib.available_tecs || [];
                devSel.innerHTML = "";
                devs.forEach(d => {
                    const opt = document.createElement("option");
                    opt.value = d;
                    opt.text  = d;
                    devSel.appendChild(opt);
                });
                if (!focusFlags["gpib-device-select"]) {
                    devSel.value = response.gpib.selected_tec || "";
                }
            }

            // sweep-active toggle
            if (!focusFlags["sweep-active"]) {
                document.getElementById("sweep-active").checked =
                    Boolean(response.gpib.temp_sweep.active);
            }

            // sweep parameters
            const sweep_params = response.gpib.temp_sweep;
            const map = {
                "sweep-active": String(sweep_params.active),
                "sweep-start":  sweep_params.t_start,
                "sweep-end":    sweep_params.t_end,
                "sweep-step":   sweep_params.t_step,
                "sweep-tol":    sweep_params.tol
            };
            for (const id in map) {
                if (!focusFlags[id]) $("#" + id).val(map[id]);
            }

            $("#tec-set").text(response.gpib.info.tec_setpoint);
            $("#tec-meas").text(response.gpib.info.tec_temp_meas);
            $("#tec-amp").text(response.gpib.info.tec_current);
            $("#tec-volt").text(response.gpib.info.tec_voltage);

        } else {
            // hide tab & pane if GPIB unavailable
            tab.style.display  = "none";
            pane.style.display = "none";
        }

        if (!focusFlags["bit-mode-dropdown"]) {$("#bit-mode-dropdown").val(response.device.settings.mode.resolution)}
        if (!focusFlags["time-base-input"]) {$("#time-base-input").val(response.device.settings.mode.timebase)}

        var chan_responses = [response.device.settings.channels.a, response.device.settings.channels.b, response.device.settings.channels.c, response.device.settings.channels.d]

        // Ensure all the channel settings match with the values from the adapter
        for (var i = 0; i < 4; i++) {
            var channel = "channel-"+String.fromCharCode(i + 97)+"-"
            if (!focusFlags[channel+"range"]) {$("#"+channel+"range").val(chan_responses[i].range)}
            if (!focusFlags[channel+"coupl"]) {$("#"+channel+"coupl").val(chan_responses[i].coupling)}
            if (!focusFlags[channel+"offset"]) {$("#"+channel+"offset").val(chan_responses[i].offset)}
            if (!focusFlags[channel+"active"]) {document.getElementById(channel+"active").checked=(chan_responses[i].active)}
            if (!focusFlags[channel+"liveview"]) {document.getElementById(channel+"liveview").checked=(chan_responses[i].live_view)}
            if (!focusFlags[channel+"pha"]) {document.getElementById(channel+"pha").checked=(chan_responses[i].pha_active)}
            activate_buttons(String.fromCharCode(i + 97), chan_responses[i].active)
        }

        // Ensure acquisition settings match adapter values
        document.getElementById("capture-mode-time").checked = response.device.settings.capture.capture_mode
        document.getElementById("capture-mode-num").checked = !(response.device.settings.capture.capture_mode)
        document.getElementById("cap-repeat").checked = response.device.settings.capture.capture_repeat

        if (!focusFlags["trigger-enable"]) {
            $("#trigger-enable").val(String(response.device.settings.trigger.active));
        }
        
        // Ensure the settings match with the values from the adapter
        var settings = response.device.settings
        var settings_2 = [settings.trigger, settings.capture, settings.file, settings.pha]
        var settings_3 = [settings_2[0].source, settings_2[0].direction, settings_2[0].threshold, settings_2[0].delay,
                        settings_2[0].auto_trigger, settings_2[1].pre_trig_samples, settings_2[1].post_trig_samples,
                        settings_2[1].n_captures, settings_2[1].capture_time, settings_2[1].repeat_amount,
                        settings_2[1].capture_delay, settings_2[2].folder_name, settings_2[2].file_name,
                        settings_2[3].num_bins, settings_2[3].lower_range, settings_2[3].upper_range]

        var focus_strings = ["trigger-source", "trigger-direction", "trigger-threshold", "trigger-delay","trigger-auto",
                        "capture-pretrig-samples", "capture-posttrig-samples", "capture-count", "capture-time",
                        "repeat-amount", "delay-time", "capture-folder-name", "capture-file-name", "pha-num-bins",
                        "pha-lower-range", "pha-upper-range"]

        for (var setting = 0; setting < focus_strings.length; setting++) {
            if (!focusFlags[focus_strings[setting]]) {$("#" + focus_strings[setting]).val(settings_3[setting])}
        }

        // Identify all of the channels that are LV active
        active_channels_lv = response.device.live_view.lv_active_channels
        active_channels_lv_letters = []
        for (let chan = 0; chan < active_channels_lv.length; chan++) {
            active_channels_lv_letters.push(String.fromCharCode(65+active_channels_lv[chan]))
        }

        // Identify all of the channels that are PHA active
        pha_channels = [response.device.settings.channels.a.pha_active, response.device.settings.channels.b.pha_active,
                response.device.settings.channels.c.pha_active, response.device.settings.channels.d.pha_active]
        active_channels_pha_letters = []
        for (let chan = 0; chan < pha_channels.length; chan++) {
            if (pha_channels[chan] == true) {
                active_channels_pha_letters.push(String.fromCharCode(65+chan))
            }
        }

        // Keep track of lower and upper PHA range, and samples
        lower_range = response.device.settings.pha.lower_range
        upper_range = response.device.settings.pha.upper_range
        pre_samples = response.device.settings.capture.pre_trig_samples
        post_samples = response.device.settings.capture.post_trig_samples
        
        chan_ranges = [chan_responses[0].range, chan_responses[1].range, chan_responses[2].range, chan_responses[3].range]

        // Define the colour to be used on the graph for different channels
        channel_colours = ['rgb(0, 110, 255)', 'rgb(255, 17, 0)', 'rgb(83, 181, 13)', 'rgb(255, 230, 0)']

        // Assign LV & PHA data locally
        try {
            if (response.device.live_view.lv_data != undefined) {
                if ((response.device.live_view.lv_data.toString()) != (lv_data.toString())) {
                    data_array = response.device.live_view.lv_data
                }
                update_lv_graph()
            }
        } catch {
            console.log("Error in assigning and plotting LV values")
        }
        
        try {
            if (response.device.live_view.pha_counts != undefined) {
                if ((response.device.live_view.pha_counts.toString()) != (pha_array.toString())) {
                    pha_array = response.device.live_view.pha_counts
                    bin_edges = response.device.live_view.pha_bin_edges
                    update_pha_graph()
                }
            }
        } catch (err){
            console.log("Error in assigning PHA values, error: ",err.message)
        }

        // If user capture is in progress, update the progress bar accordingly
        if (response.device.commands.run_user_capture == true){

            lock_boxes(true)

            if (response.device.settings.capture.capture_mode == true) {
                var cap_percent = ((response.device.live_view.current_tbdc_time / response.device.settings.capture.capture_time) * (100 / response.device.settings.capture.repeat_amount)).toFixed(2)
                console.log("percent: ", cap_percent)
            } else {
                var cap_percent = ((response.device.live_view.capture_count / response.device.live_view.captures_requested) * (100 / response.device.settings.capture.repeat_amount)).toFixed(2)
            }

            var current_cap = response.device.live_view.current_capture

            var percent_done = ((current_cap / response.device.settings.capture.repeat_amount) * 100).toFixed(2)
            percent_done = parseFloat(percent_done)
            cap_percent = parseFloat(cap_percent)

            cap_percent = (cap_percent + percent_done)

            let progressBar = document.getElementById('capture-progress-bar');
            progressBar.style.width = cap_percent + '%';
            progressBar.innerHTML = cap_percent + '%';
        } else {
            lock_boxes(false)

            let progressBar = document.getElementById('capture-progress-bar');
            progressBar.style.width = 0 + '%';
            progressBar.innerHTML = 0 + '%';

            // Only allow the user to enter repetition settings if the repetition setting is on
            if (response.device.settings.capture.capture_repeat == true) {
                document.getElementById("repeat-amount").disabled = false
                document.getElementById("delay-time").disabled = false
            } else {
                document.getElementById("repeat-amount").disabled = true
                document.getElementById("delay-time").disabled = true
            }

            // Only allow the relevant boxes to be open, depending on capture mode chosen
            if (response.device.settings.capture.capture_mode == true) {
                document.getElementById("capture-count").disabled = true
                document.getElementById("capture-time").disabled = false
            } else {
                document.getElementById("capture-count").disabled = false
                document.getElementById("capture-time").disabled = true
            }
        }

        document.getElementById("samp-int").textContent = toSiUnit(response.device.settings.mode.samp_time)
        folder_name = response.device.settings.file.folder_name  //document.getElementById("capture-folder-name").textContent
        if ((folder_name[folder_name.length - 1] == '/') || (folder_name.length == 0)) {
            document.getElementById("file-name-span").textContent = ('data/' + response.device.settings.file.folder_name + response.device.settings.file.file_name)
        } else {
            document.getElementById("file-name-span").textContent = ('data/' + response.device.settings.file.folder_name + '/' + response.device.settings.file.file_name)
        }

        // Update the recommended capture amount and time length
        document.getElementById("suggest-caps").textContent = response.device.settings.capture.max_captures
        document.getElementById("suggest-time").textContent = response.device.settings.capture.max_time

        // Display a N/A recommended caps/time if no channels are active
        if (document.getElementById("suggest-caps").textContent == "0") {
            document.getElementById("suggest-caps").textContent = "N / A"
            document.getElementById("suggest-time").textContent = "N / A"
        }

        // Display the 'recorded' attribute as true if a capture has been recorded successfully
        if (response.device.settings.file.last_write_success == true){
            document.getElementById("file-write-succ-span").textContent = "True"
        } else {
            document.getElementById("file-write-succ-span").textContent = "False"
        }

        // Check if settings have been verified
        if (response.device.status.pico_setup_verify == 0){
            document.getElementById("general-setup-row").className="success"
        }else{
            document.getElementById("general-setup-row").className="danger"
        }

        document.getElementById("chan-row").className = "danger"

        // Syncing channel setup panels
        if ((response.device.settings.channels.a.verified == true) && (response.device.settings.channels.a.active == true)) {
            document.getElementById("channel-a-set").className ="success"
            document.getElementById("chan-row").className = "success"
        } else{
            document.getElementById("channel-a-set").className ="danger"
        }
        
        if ((response.device.settings.channels.b.verified == true) && (response.device.settings.channels.b.active == true)) {
            document.getElementById("channel-b-set").className ="success"
            document.getElementById("chan-row").className = "success"
        } else{
            document.getElementById("channel-b-set").className ="danger";
        }
            
        if ((response.device.settings.channels.c.verified == true) && (response.device.settings.channels.c.active == true)) {
            document.getElementById("channel-c-set").className ="success";
            document.getElementById("chan-row").className = "success"
        } else{
            document.getElementById("channel-c-set").className ="danger";
        }

        if ((response.device.settings.channels.d.verified == true) && (response.device.settings.channels.d.active == true)) {
            document.getElementById("channel-d-set").className ="success";
            document.getElementById("chan-row").className = "success"
        } else{
            document.getElementById("channel-d-set").className ="danger";
        }

        // Check if trigger settings have been verified
        if (response.device.status.channel_trigger_verify == 0){
            document.getElementById("trigger-row1").className ="success";
            document.getElementById("trigger-row2").className ="success";

        } else{
            document.getElementById("trigger-row1").className ="danger";
            document.getElementById("trigger-row2").className ="danger";
        }

        // Check if capture settings have been verified, change colour of boxes accordingly
        if (response.device.status.capture_settings_verify == 0){
            document.getElementById("pha-row").className ="success";
            document.getElementById("capture-row").className = "success"
            document.getElementById("file-row").className = "success"
            document.getElementById("file-info-row").className = "success"
            document.getElementById("repeat-cap-row").className = "success"
            if (response.device.commands.run_user_capture == true) {
                document.getElementById("cap-progress").className = "success"
            } else {
                document.getElementById("cap-progress").className = ""
            }
        } else {
            document.getElementById("cap-progress").className = "danger"
            document.getElementById("pha-row").className ="danger";
            document.getElementById("capture-row").className = "danger"
            document.getElementById("file-row").className = "danger"
            document.getElementById("file-info-row").className = "danger"
            document.getElementById("repeat-cap-row").className = "danger"
        }

        // Check if PicoScope unit has been opened, and connection has been established
        if (response.device.status.open_unit == 0){
            document.getElementById("connection_status").textContent = "True"
        } else {
            document.getElementById("connection_status").textContent = "False"
        }

        // Change the capture type displayed depending on which capture type is being utilised
        if (response.device.commands.run_user_capture == true){
            document.getElementById("cap_type_status").textContent = "User"
        } else if (response.device.commands.time_capture == true){
            document.getElementById("cap_type_status").textContent = "Time-Based"
        } else if (response.device.commands.live_view_active) {
            document.getElementById("cap_type_status").textContent = "Live View"
        }

        if (response.device.status.settings_verified == true){
            document.getElementById("settings_status").textContent = "True"
        } else {
            document.getElementById("settings_status").textContent = "False"
        }
        document.getElementById("system-state").textContent = response.device.flags.system_state
    }
}

function disable_id(id,bool){
    document.getElementById(id).disabled = bool;
}

function run_pico_command(){
    var value = 0
    ajax_put('commands/','run_capture',value)
}

function commit_true_adapter(path,key){
    ajax_put(path,key,true)
}

function commit_to_adapter(id,path,key){
    // Commit a boolean value to adapter
    var value = document.getElementById(id).value
    if (value == "true"){ value = true}
    if (value == "false"){ value = false}
    console.log(path,key,value)
    ajax_put(path,key,value)
}

function commit_int_adapter(id,path,key){
    // Commit integer value to adapter
    var input = parseInt(document.getElementById(id).value)
    if (isNaN(input)){
        console.log("Invalid")
    } else {
        ajax_put(path,key,input)
    }
}

function commit_str_adapter(id,path,key){
    // Commit string value to adapter
    var input = document.getElementById(id).value
    ajax_put(path,key,input)
}

function commit_float_adapter(id,path,key){
    // Commit float value to adapter
    var input = parseFloat(document.getElementById(id).value)
    if (isNaN(input)){
        console.log("Invalid")
    } else {
        ajax_put(path,key,input)
    }
}

function commit_checked_adapter(id,path,key){
    var checked = document.getElementById(id).checked
    ajax_put(path,key,checked)

    if (key == "capture_mode") {
        activate_textbox(checked)
    }
}

function activate_buttons(channel, checked) {
    // Activate/deactivate buttons depending on whether it's channel is active
    document.getElementById("channel-"+channel+"-liveview").disabled = !checked
    document.getElementById("channel-"+channel+"-pha").disabled = !checked
}

function activate_textbox(checked) {
    // Activate/deactivate textboxes depending on capture mode chosen
    if (checked == false) {
        document.getElementById("cap-label").textContent = "No. Captures"
    } else {
        document.getElementById("cap-label").textContent = "Time Capture"
    }
}

function lock_boxes(lock) {
    // Lock boxes if a capture is currently in progress
    buttons = ["bit-mode-dropdown", "time-base-input", "capture-pretrig-samples", "capture-posttrig-samples",
            "channel-a-active", "channel-a-coupl", "channel-a-range", "channel-a-offset",
            "channel-b-active", "channel-b-coupl", "channel-b-range", "channel-b-offset",
            "channel-c-active", "channel-c-coupl", "channel-c-range", "channel-c-offset",
            "channel-d-active", "channel-d-coupl", "channel-d-range", "channel-d-offset", 
            "trigger-enable", "trigger-source", "trigger-direction", "trigger-threshold",
            "trigger-delay", "trigger-auto", "pha-num-bins", "pha-lower-range", "pha-upper-range",
            "capture-mode-num", "capture-mode-time", "cap-repeat", "capture-folder-name", "capture-file-name",
            "gpib-enable", "gpib-device-select", "sweep-active","sweep-start", "sweep-end", 
            "sweep-step", "sweep-tol"]
    
    if (lock == true) {
        buttons.push("repeat-amount", "delay-time", "capture-count", "capture-time")
        // disable GPIB controls during a capture
        // buttons.push("gpib-enable", "gpib-device-select", "sweep-active","sweep-start", "sweep-end", 
        //     "sweep-step", "sweep-tol");
    }

    for (var i = 0; i < buttons.length; i++) {
        document.getElementById(buttons[i]).disabled = lock
    }
}

function verify_int(id){
    var input_box = (document.getElementById(id));
    var regexCurr = /^[0-9]+$/;
    if (regexCurr.test(input_box.value)){
        return 1
    } else {
        input_box.value = "";
        return 0 
    }       
}

function verify_float(id){
    var input_box = (document.getElementById(id));
    var regex_float = /^[+-]?(?:\d*\.)?\d+$/;
    if (regex_float.test(input_box.value)){
        return 1
    } else {
        input_box.value = "";
        return 0
    }       
}

function toSiUnit(num){
    numin = num
    pow = [-15,-12,-9,-6,-3,0]
    siUnit = ['f','p','n','μ','m','']
    i=5
    isNegative = numin < 0;
    if (isNegative) {
        numin = -numin;
    }
    testnum = (numin / (Math.pow(10,pow[i])))
    while ( testnum < 1){
        i = i -1
        testnum = (numin / (Math.pow(10,pow[i])))
    }
    if (isNegative) {
        return(('-'+testnum.toFixed(2))+' '+siUnit[i])
    } else{
        return((testnum.toFixed(2))+' '+siUnit[i])
    }
}

function ajax_put(path, key, value) {
    // Put function for adapter, prevents repetition of code
    let data = {};
    data[key] = value;

    // choose prefix automatically 
    const prefix = path.startsWith("gpib/") ? "" : "device/";

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/pico/' + prefix + path,
        contentType: "application/json",
        data: JSON.stringify(data),
    });
}

function openTab(tabID) {
    // Close one tab, and open another
    var one   = document.getElementById("one");
    var two   = document.getElementById("two");
    var three = document.getElementById("three");

    if (tabID == "one") {
        one.style.display   = "block";
        two.style.display   = "none";
        if (three) three.style.display = "none";
    } else if (tabID == "two") {
        one.style.display   = "none";
        two.style.display   = "block";
        if (three) three.style.display = "none";
    } else if (tabID == "three") {
        one.style.display   = "none";
        two.style.display   = "none";
        if (three) three.style.display = "block";
    }
}
