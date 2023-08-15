api_version = '0.1';
page_not_loaded = true;

data_array = new Int16Array()
counts = new Int16Array()
bin_edges = new Int16Array()
play_button = true;

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

function toggle_play() {
    const button = document.getElementById('p_p_button');
    play_button = !play_button;
    
    if (play_button) {
      button.innerHTML = '<span class="material-icons">pause</span>'; 
    } else {
      button.innerHTML = '<span class="material-icons">play_arrow</span>';
    }
  }

function plotly_liveview(ranges){
    channel = parseInt(document.getElementById('lv-source').value)
    let range = get_range_value_mv(ranges[channel])

    var tickVals = [];
    var tickText = [];
    var stepSize = 2 * range / 8;

    for (var i = -range; i <= range; i += stepSize) {
        tickVals.push(i);
        tickText.push(i.toFixed(2)); 
    }

    if (play_button){
        scope_lv = document.getElementById('scope_lv');
        Plotly.newPlot( scope_lv, [{
            x: x = data_array.map((value, index) => index),                
            y: data_array }], {
                title: 'Live view of PicoScope traces',
                margin: { t: 40, b: 40 },
                xaxis: { title: 'Sample Interval' },
                yaxis: { title: 'Voltage (mV)',
                        range: [-range, range],
                        tickvals: tickVals,
                        ticktext: tickText } });

        scope_pha = document.getElementById('scope_pha');
        Plotly.newPlot( scope_pha, [{
            x: bin_edges,
            y: counts }], {
                title: 'Last PHA from recorded traces',
                margin: { t: 40, b: 40 },
                yaxis: { title: 'Counts'},
                xaxis: { title: 'Energy level (ADC_Counts)'} });
    }
    else {
        return;
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
        if (page_not_loaded == true){
            $("#bit-mode-dropdown").val(response.device.settings.mode.resolution)
            $("#time-base-input").val(response.device.settings.mode.timebase)

            document.getElementById("channel-a-active").checked=(response.device.settings.channels.a.active)
            document.getElementById("channel-b-active").checked=(response.device.settings.channels.b.active)
            document.getElementById("channel-c-active").checked=(response.device.settings.channels.c.active)
            document.getElementById("channel-d-active").checked=(response.device.settings.channels.d.active)

            $("#channel-a-coupl").val(response.device.settings.channels.a.coupling)
            $("#channel-b-coupl").val(response.device.settings.channels.b.coupling)
            $("#channel-c-coupl").val(response.device.settings.channels.c.coupling)
            $("#channel-d-coupl").val(response.device.settings.channels.d.coupling)

            $("#channel-a-range").val(response.device.settings.channels.a.range)
            $("#channel-b-range").val(response.device.settings.channels.b.range)
            $("#channel-c-range").val(response.device.settings.channels.c.range)
            $("#channel-d-range").val(response.device.settings.channels.d.range)

            $("#channel-a-range").val(response.device.settings.channels.a.range)
            $("#channel-b-range").val(response.device.settings.channels.b.range)
            $("#channel-c-range").val(response.device.settings.channels.c.range)
            $("#channel-d-range").val(response.device.settings.channels.d.range)

            $("#channel-a-offset").val(response.device.settings.channels.a.offset)
            $("#channel-b-offset").val(response.device.settings.channels.b.offset)
            $("#channel-c-offset").val(response.device.settings.channels.c.offset)
            $("#channel-d-offset").val(response.device.settings.channels.d.offset)

            if (response.device.settings.trigger.active == true){$("#trigger-enable").val("true")}
            if (response.device.settings.trigger.active == false){$("#trigger-enable").val("false")}
            $("#trigger-source").val(response.device.settings.trigger.source)
            $("#trigger-direction").val(response.device.settings.trigger.direction)
            $("#trigger-threshold").val(response.device.settings.trigger.threshold)
            $("#trigger-delay").val(response.device.settings.trigger.delay)
            $("#trigger-auto").val(response.device.settings.trigger.auto_trigger)

            $("#capture-pretrig-samples").val(response.device.settings.capture.pre_trig_samples)
            $("#capture-posttrig-samples").val(response.device.settings.capture.post_trig_samples)
            $("#capture-count").val(response.device.settings.capture.n_captures)

            $("#capture-folder-name").val(response.device.settings.file.folder_name)
            $("#capture-file-name").val(response.device.settings.file.file_name)
            page_not_loaded = false;
        }

        // Check the lv_data array contains data, if it does, assign the data locally
        try{
            if ((response.device.live_view.lv_data).length != 0) {
                data_array = response.device.live_view.lv_data
            } else {
                console.log("\n\nEmpty LV Array not updating graph")
            }
        } catch {
                console.log("Error in assigning LV values")
            }

        try{   
            if ((response.device.live_view.pha_data).length != 0){
                bin_edges = response.device.live_view.pha_data[0]
                counts = response.device.live_view.pha_data[1]
                console.log("PHA DATA:",bin_edges[50], counts[50])
                console.log("pha response: ", response.device.live_view.pha_data)
            } else {
                console.log("\n\nEmpty PHA Array not updating graph")
            }

        } catch (err){
            console.log("Error in assigning PHA values, error: ",err.message)
        }
        
        let cap_percent = ((100/response.device.live_view.captures_requested) * response.device.live_view.capture_count).toFixed(2)
        let progressBar = document.getElementById('capture-progress-bar');
        progressBar.style.width = cap_percent + '%';
        progressBar.innerHTML = cap_percent + '%';
        
        document.getElementById("samp-int").textContent = toSiUnit(response.device.settings.mode.samp_time)

        document.getElementById('lv-source').value = response.device.live_view.preview_channel
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

            ranges=[response.device.settings.channels.a.range, response.device.settings.channels.b.range,
                response.device.settings.channels.c.range, response.device.settings.channels.d.range]
            plotly_liveview(ranges);
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
    console.log(input)
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