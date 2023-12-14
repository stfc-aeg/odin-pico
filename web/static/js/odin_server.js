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
};
// Initialize a timers object to keep track of the timers for each field
var timers = {};

// Time limit (in milliseconds) after which to blur the input
var timeLimit = 10000; // 5 seconds

var pha_array = []
var lv_data = []
var active_channels_lv = []
var chan_ranges = [0, 0, 0, 0]

play_button_lv = true;
play_button_pha = true;

//runs when the script is loaded
$( document ).ready(function() {
    update_api_version();
    update_lv_graph();
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
            xaxis: {title: 'Energy Level (ADC_Counts)'},
            yaxis: {title: 'Counts'},
            autosize: true,
            legend: {orientation: "h"}
        }
        Plotly.newPlot((document.getElementById('scope_pha')), pha_data, layout, {scrollZoom: true})
    }
}

function update_lv_graph(){
    console.log("DOING LV")
    if (play_button_lv){
        console.log("YES")
        try {
            // Create variables for values on graph axes
            var tickVals = [];
            var tickText = [];

            lv_data = []

            layout = {
                title: 'Live view of PicoScope traces',
                margin: { t: 50, b: 60 },
                xaxis: { title: 'Sample Interval'},
                yaxis: { title: ('Channel  Voltage (mV)')},
                autosize: true
            }

            if (active_channels_lv.length > 0) {

                // Fetch channel range for first LV channel
                let range1 = get_range_value_mv(chan_ranges[(active_channels_lv[0])])

                // Create first data line
                var trace_one = {
                    x: x = data_array[0].map((value, index)=> index),
                    y: y = data_array[0],
                    name: ('Channel ' + active_channels_lv_letters[0]),
                    type: 'scatter',
                    line: {color: channel_colours[active_channels_lv[0]]}
                }

                // Create the values to go on graph axes
                var stepSize = range1 / 4
                for (var i = -range1; i <= range1; i += stepSize) {
                    tickVals.push(i);
                    tickText.push(i.toFixed(1)); 
                }

                // Create the layout for the graph
                layout = {
                    title: 'Live view of PicoScope traces',
                    margin: { t: 50, b: 60 },
                    xaxis: { title: 'Sample Interval'},
                    yaxis: {
                        title: ('Channel ' + active_channels_lv_letters[0] + ' Voltage (mV)'),
                        range: [-range1, range1],
                        tickvals: tickVals,
                        ticktext: tickText,
                    },
                    autosize: true
                }

                // Push the data from trace_one into the lv_data list
                lv_data.push(trace_one)
                if (active_channels_lv.length > 1) {

                    var tickVals2 = [];
                    var tickText2 = [];           

                    // Fetch channel range for second LV channel
                    let range2 = get_range_value_mv(chan_ranges[(active_channels_lv[1])])

                    // Create the second data line for the graph
                    var trace_two = {
                        x: x = data_array[1].map((value, index) => index),
                        y: data_array[1],
                        name: ('Channel ' + active_channels_lv_letters[1]),
                        yaxis: 'y2',
                        type: 'scatter',
                        line: {color: channel_colours[active_channels_lv[1]]}
                    }

                    // Create labels for graph axes
                    var stepSize2 = range2 / 4
                    for (var i = -range2; i <= range2; i += stepSize2) {
                        tickVals2.push(i);
                        tickText2.push(i.toFixed(1)); 
                    }

                    // Add second data line to lv_data
                    lv_data.push(trace_two)

                    // Create layout for plotly graph, with two axes
                    layout = {
                        title: 'Live view of PicoScope traces',
                        margin: { t: 50, b: 60},
                        xaxis: { title: 'Sample Interval'},
                        yaxis: {
                            title: ('Channel ' + active_channels_lv_letters[0] +  ' Voltage (mV)'),
                            automargin: true,
                            range: [-range1, range1],
                            tickvals: tickVals,
                            ticktext: tickText,
                        },
                        yaxis2: {
                            title: ('Channel ' + active_channels_lv_letters[1] + ' Voltage (mV)'),
                            range:[-range2, range2],
                            overlaying: 'y',
                            side: 'right',
                            tickvals: tickVals2,
                            ticktext: tickText2,
                            autosize: true,
                        },
                        legend: {
                            orientation: "h",
                        }
                    }
                }
            }
            Plotly.newPlot((document.getElementById('scope_lv')), lv_data, layout, {scrollZoom: true})
        } catch (TypeError) {
            console.log("TypeError identified")
        }
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
            activate_lv_buttons(String.fromCharCode(i + 97), chan_responses[i].active)
            if (pha_array != undefined) {
                try{
                    if (pha_array[i].length != 0) {
                        activate_pha_buttons(String.fromCharCode(i + 97), true)
                    }
                    else {
                        activate_pha_buttons(String.fromCharCode(i + 97), false)
                    }
                } catch {}
            }
        }

        if (!focusFlags["trigger-enable"]) {
            if (response.device.settings.trigger.active == true) {$("#trigger-enable").val("true")}
            if (response.device.settings.trigger.active == false) {$("#trigger-enable").val("false")}
        }
        
        if (!focusFlags["trigger-source"]) {$("#trigger-source").val(response.device.settings.trigger.source)}
        if (!focusFlags["trigger-direction"]) {$("#trigger-direction").val(response.device.settings.trigger.direction)}
        if (!focusFlags["trigger-threshold"]) {$("#trigger-threshold").val(response.device.settings.trigger.threshold)}
        if (!focusFlags["trigger-delay"]) {$("#trigger-delay").val(response.device.settings.trigger.delay)}
        if (!focusFlags["trigger-auto"]) {$("#trigger-auto").val(response.device.settings.trigger.auto_trigger)}
        
        if (!focusFlags["capture-pretrig-samples"]) {$("#capture-pretrig-samples").val(response.device.settings.capture.pre_trig_samples)}
        if (!focusFlags["capture-posttrig-samples"]) {$("#capture-posttrig-samples").val(response.device.settings.capture.post_trig_samples)}
        if (!focusFlags["capture-count"]) {$("#capture-count").val(response.device.settings.capture.n_captures)}
        
        if (!focusFlags["capture-folder-name"]) {$("#capture-folder-name").val(response.device.settings.file.folder_name)}
        if (!focusFlags["capture-file-name"]) {$("#capture-file-name").val(response.device.settings.file.file_name)}
        
        if (!focusFlags["pha-num-bins"]) {$("#pha-num-bins").val(response.device.settings.pha.num_bins)}
        if (!focusFlags["pha-lower-range"]) {$("#pha-lower-range").val(response.device.settings.pha.lower_range)}
        if (!focusFlags["pha-upper-range"]) {$("#pha-upper-range").val(response.device.settings.pha.upper_range)}

        active_channels_lv = response.device.live_view.active_channels
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
        
        channel_colours = ['rgb(0, 110, 255)', 'rgb(255, 17, 0)', 'rgb(83, 181, 13)', 'rgb(252, 232, 5)']

        max_adc = response.device.settings.pha.upper_range
        min_adc = response.device.settings.pha.lower_range
        chan_ranges=[response.device.settings.channels.a.range, response.device.settings.channels.b.range,
            response.device.settings.channels.c.range, response.device.settings.channels.d.range]
        chan_offsets = [response.device.settings.channels.a.offset, response.device.settings.channels.b.offset,
            response.device.settings.channels.c.offset, response.device.settings.channels.d.offset]
        // Assign LV & PHA data locally
        try {
            console.log("HERE")
            if (response.device.live_view.lv_data != undefined) {
                console.log("HERE 1")
                if ((response.device.live_view.lv_data.toString()) != (lv_data.toString())) {
                    console.log("HERE 2")
                    data_array = response.device.live_view.lv_data
                    update_lv_graph()
                } else {
                    console.log("HERE 2")
                    update_lv_graph()
                }
            }              
        } catch {
            console.log("Error in assigning LV values")
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
        } else {
            document.getElementById("cap_type_status").textContent = "LiveView"
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

function activate_lv_buttons(channel, checked) {
    document.getElementById("channel-"+channel+"-liveview").disabled = !checked
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

function ajax_get(path,key){

}