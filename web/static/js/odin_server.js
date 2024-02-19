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
  "lv_range": false,
};
// Initialize a timers object to keep track of the timers for each field
var timers = {};

// Time limit (in milliseconds) after which to blur the input
var timeLimit = 10000; // 5 seconds

var pha_array = []
var lv_data = []
var active_channels_lv = []

play_button_lv = true;
play_button_pha = true;

//runs when the script is loaded
$( document ).ready(function() {
    update_api_version();
    run_sync();
});

//gets the most up to date api version
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
    
    if (play_button_lv) {
      button_lv.innerHTML = '<span class="material-icons">pause_circle_outline</span>'; 
    } else {
      button_lv.innerHTML = '<span class="material-icons">play_circle_outline</span>';
    }
  }

function toggle_play_pha() {
    const button_pha = document.getElementById('p_p_button_pha');
    play_button_pha = !play_button_pha;

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

        Plotly.newPlot((document.getElementById('scope_pha')), pha_data, layout, {scrollZoom: true})
    }
}

function update_lv_graph() {

    if (play_button_lv) {

        var tickText = []
        var tickVals = []

        let range = get_range_value_mv(lv_range)

        lv_data = []

        for (var i = -range; i <= range; i += (range / 4)) {
            tickVals.push(i);
            tickText.push(i.toFixed(1)); 
        }

        layout = {
            title: 'Live view of PicoScope traces',
            margin: { t: 50, b: 60 },
            xaxis: {
                title: 'Sample Interval',
                range: [pre_samples, post_samples],
            },
            yaxis: {
                title: ('Channel  Voltage (mV)'),
                range: [-range, range],
                ticktext: tickText,
                tickvals: tickVals,
            },
            autosize: true,
            showlegend: true
        }

        for (var chan = 0; chan < active_channels_lv.length; chan++) {
            lv_data.push ({
                x: x = data_array[chan].map((value, index)=> index),
                y: y = data_array[chan],
                name: ('Channel '+ active_channels_lv_letters[chan]),
                type: 'scatter',
                line: {color: channel_colours[active_channels_lv[chan]]}
            })
        }

        Plotly.newPlot((document.getElementById('scope_lv')), lv_data, layout, {scrollZoom: true})
    }
}

function run_sync(){
    $.getJSON('/api/' + api_version + '/pico/device/', sync_with_adapter());
    setTimeout(run_sync, 150);
}

function get_range_value_mv(key) {
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

        if (!focusFlags["bit-mode-dropdown"]) {$("#bit-mode-dropdown").val(response.device.settings.mode.resolution)}
        
        if (!focusFlags["time-base-input"]) {$("#time-base-input").val(response.device.settings.mode.timebase)}

        var chan_responses = [response.device.settings.channels.a, response.device.settings.channels.b, response.device.settings.channels.c, response.device.settings.channels.d]

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

        if (!focusFlags["trigger-enable"]) {
            if (response.device.settings.trigger.active == true) {$("#trigger-enable").val("true")}
            if (response.device.settings.trigger.active == false) {$("#trigger-enable").val("false")}
        }
        
        var settings = response.device.settings
        
        var settings_2 = [settings.trigger, settings.capture, settings.file, settings.pha]

        var settings_3 = [settings_2[0].source, settings_2[0].direction, settings_2[0].threshold, settings_2[0].delay,
                        settings_2[0].auto_trigger, settings_2[1].pre_trig_samples, settings_2[1].post_trig_samples,
                        settings_2[1].n_captures, settings_2[2].folder_name, settings_2[2].file_name, settings_2[3].num_bins,
                        settings_2[3].lower_range, settings_2[3].upper_range]

        var focus_strings = ["trigger-source", "trigger-direction", "trigger-threshold", "trigger-delay","trigger-auto",
                        "capture-pretrig-samples", "capture-posttrig-samples", "capture-count", "capture-folder-name",
                        "capture-file-name", "pha-num-bins", "pha-lower-range", "pha-upper-range"]

        for (var setting = 0; setting < focus_strings.length; setting++) {
            if (!focusFlags[focus_strings[setting]]) {$("#" + focus_strings[setting]).val(settings_3[setting])}
        }

        if (!focusFlags["lv_range"]) {$("#lv_range").val(response.device.live_view.lv_range)}

        active_channels_lv = response.device.live_view.lv_active_channels
        active_channels_lv_letters = []
        for (let chan = 0; chan < active_channels_lv.length; chan++) {
            active_channels_lv_letters.push(String.fromCharCode(65+active_channels_lv[chan]))
        }

        pha_channels = [response.device.settings.channels.a.pha_active, response.device.settings.channels.b.pha_active,
                response.device.settings.channels.c.pha_active, response.device.settings.channels.d.pha_active]
        active_channels_pha_letters = []
        for (let chan = 0; chan < pha_channels.length; chan++) {
            if (pha_channels[chan] == true) {
                active_channels_pha_letters.push(String.fromCharCode(65+chan))
            }
        }

        lower_range = response.device.settings.pha.lower_range
        upper_range = response.device.settings.pha.upper_range

        pre_samples = response.device.settings.capture.pre_trig_samples
        post_samples = response.device.settings.capture.post_trig_samples
        
        channel_colours = ['rgb(0, 110, 255)', 'rgb(255, 17, 0)', 'rgb(83, 181, 13)', 'rgb(252, 232, 5)']

        lv_range = response.device.live_view.lv_range

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
        
        if (response.device.commands.run_user_capture == true){
            let cap_percent = ((100/response.device.live_view.captures_requested) * response.device.live_view.capture_count).toFixed(2)
            let progressBar = document.getElementById('capture-progress-bar');
            progressBar.style.width = cap_percent + '%';
            progressBar.innerHTML = cap_percent + '%';
        } else {
            let progressBar = document.getElementById('capture-progress-bar');
            progressBar.style.width = 0 + '%';
            progressBar.innerHTML = 0 + '%';
        }

        document.getElementById("samp-int").textContent = toSiUnit(response.device.settings.mode.samp_time)
        document.getElementById("file-name-span").textContent = response.device.settings.file.curr_file_name
        if (response.device.settings.file.last_write_success == true){
            document.getElementById("file-write-succ-span").textContent = "True"
        } else {
            document.getElementById("file-write-succ-span").textContent = "False"
        }

        if (response.device.status.pico_setup_verify == 0){
            document.getElementById("pico-setup-row").className="success"
        }else{
            document.getElementById("pico-setup-row").className="danger"
        }

        // Syncing channel setup panels
        if (response.device.settings.channels.a.verified == true){
            document.getElementById("channel-a-set").className ="success"
            } else{
                document.getElementById("channel-a-set").className ="danger"
            }
        

        if (response.device.settings.channels.b.verified == true){
            document.getElementById("channel-b-set").className ="success"
            } else{
                document.getElementById("channel-b-set").className ="danger";
            }
            
        if (response.device.settings.channels.c.verified == true){
            document.getElementById("channel-c-set").className ="success";
            } else{
                document.getElementById("channel-c-set").className ="danger";
            }

        if (response.device.settings.channels.d.verified == true){
        document.getElementById("channel-d-set").className ="success";
        } else{
            document.getElementById("channel-d-set").className ="danger";
        }

        if (response.device.status.channel_trigger_verify == 0){
            document.getElementById("trigger-row1").className ="success";
            document.getElementById("trigger-row2").className ="success";

        } else{
            document.getElementById("trigger-row1").className ="danger";
            document.getElementById("trigger-row2").className ="danger";
        }

        if (response.device.status.capture_settings_verify == 0){
        document.getElementById("capture-row").className ="success";
        } else {
            document.getElementById("capture-row").className ="danger";

        }

        if (response.device.status.open_unit == 0){
            document.getElementById("connection_status").textContent = "True"
        } else {
            document.getElementById("connection_status").textContent = "False"
        }

        if (response.device.commands.run_user_capture == true){
            document.getElementById("cap_type_status").textContent = "User"
        } else if (response.device.commands.time_capture == true){
            document.getElementById("cap_type_status").textContent = "Time-Based"
        } else if (response.device.commands.test_run == true) {
            document.getElementById("cap_type_status").textContent = "Test Run"
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
    var value = document.getElementById(id).value
    if (value == "true"){ value = true}
    if (value == "false"){ value = false}
    console.log(path,key,value)
    ajax_put(path,key,value)
}

function commit_int_adapter(id,path,key){
    var input = parseInt(document.getElementById(id).value)
    console.log("Input: ",input,typeof(input))
    if (isNaN(input)){
        console.log("Invalid")
    } else {
        console.log("Valid")
        ajax_put(path,key,input)
    }
}

function commit_str_adapter(id,path,key){
    var input = document.getElementById(id).value
    ajax_put(path,key,input)
}

function commit_float_adapter(id,path,key){
    var input = parseFloat(document.getElementById(id).value)
    if (isNaN(input)){
        console.log("Invalid")
    } else {
        console.log("Valid")
        ajax_put(path,key,input)
    }
}

function commit_checked_adapter(id,path,key){
    var checked = document.getElementById(id).checked
    ajax_put(path,key,checked)
}

function activate_buttons(channel, checked) {
    document.getElementById("channel-"+channel+"-liveview").disabled = !checked
    document.getElementById("channel-"+channel+"-pha").disabled = !checked
}

function activate_pha_buttons(channel, checked) {
    document.getElementById("channel-"+channel+"-pha").disabled = !checked
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

// May be useful to keep for picoscope ?
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

// Makes writing an ajax_put cleaner
function ajax_put(path,key,value){
    let data = {};
    data[key] = value;
    console.log(data,"data in ajax_put",JSON.stringify(data))
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/pico/device/' + path,
        contentType: "application/json",
        data: JSON.stringify(data),
    });
}
