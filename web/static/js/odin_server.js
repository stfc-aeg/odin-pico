api_version = '0.1';
page_not_loaded = true;
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

function run_sync(){
    $.getJSON('/api/' + api_version + '/pico/device/', sync_with_adapter());
    setTimeout(run_sync, 500);
}

function sync_with_adapter(){
    return function(response){
        if (page_not_loaded == true){
            $("#bit-mode-dropdown").val(response.device.connection.resolution)
            $("#time-base-input").val(response.device.settings.timebase)

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
            page_not_loaded = false;
        }      

        if (response.device.connection.resolution && ((response.device.connection.connect) == -1)){
            disable_id("connect_butt",false)
            //document.getElementById("connect_butt").disabled = false;
        }
        if (response.device.status.openunit == 0){
            //Disable 1st setup panel
            $("#status_con_attempt").html("True");
            disable_setup_1(true);
            document.getElementById("setup-1").className ="panel panel-success" 
 
            // Enable 2nd setup panel
            disable_setup_2(false); 
            document.getElementById("setup-2").className ="panel panel-danger"

        } else {
            $("#status_con_attempt").html("False");
            disable_id("bit-mode-dropdown",false);
            document.getElementById("setup-1").className ="panel panel-danger"

            disable_setup_2(true);
            document.getElementById("setup-2").className ="panel panel-default"
        }
        if (response.device.status.pico_setup_verify == 0 && response.device.status.openunit == 0){
            document.getElementById("pico-setup-row").className="success"
            disable_id("commit_chan_active_butt",false);  
        }
        if (response.device.status.pico_setup_verify == -1 && response.device.status.openunit == 0){
            document.getElementById("pico-setup-row").className="danger"
            disable_id("commit_chan_active_butt",true);
        }
        if (response.device.status.pico_setup_complete == 0){
            disable_setup_2(true);
            document.getElementById("setup-2").className ="panel panel-success"

            // Syncing channel setup panels
            if (document.getElementById("channel-a-active").checked){
                disable_setup_3_chan("a",false);
                if (response.device.settings.channels.a.verified == true){
                    document.getElementById("channel-a-set").className ="success"
                    } else{
                        document.getElementById("channel-a-set").className ="danger"
                    }
            }
            if (document.getElementById("channel-b-active").checked){
                disable_setup_3_chan("b",false);
                if (response.device.settings.channels.b.verified == true){
                    document.getElementById("channel-b-set").className ="success"
                    } else{
                        document.getElementById("channel-b-set").className ="danger";
                    }
            }
            if (document.getElementById("channel-c-active").checked){
                disable_setup_3_chan("c",false);
                if (response.device.settings.channels.c.verified == true){
                    document.getElementById("channel-c-set").className ="success";
                    } else{
                        document.getElementById("channel-c-set").className ="danger";
                    }
            }
            if (document.getElementById("channel-d-active").checked){
                disable_setup_3_chan("d",false);
                if (response.device.settings.channels.d.verified == true){
                document.getElementById("channel-d-set").className ="success";
                } else{
                    document.getElementById("channel-d-set").className ="danger";
                }
            }
            if (response.device.status.channel_setup_verify == 0){
                disable_id("commit_chan_setting_butt",false);
            } else {
                disable_id("commit_chan_setting_butt",true);
            }

            if (response.device.status.channel_setup_complete == 0 && response.device.status.pico_setup_complete == 0){
                document.getElementById("setup-3").className="panel panel-success"
                disable_setup_3(true);
            }
            if (response.device.status.channel_setup_complete == -1 && response.device.status.pico_setup_complete == 0){
                document.getElementById("setup-3").className="panel panel-danger"
            }

            } else {
                disable_setup_3(true);
            }

            if (response.device.status.channel_setup_complete == 0 && response.device.status.channel_trigger_complete == -1){
                disable_setup_4(false);
                document.getElementById("setup-4").className="panel panel-danger"
                if (response.device.status.channel_trigger_verify == 0){
                    document.getElementById("trigger-row1").className ="success";
                    document.getElementById("trigger-row2").className ="success";
                    disable_id("trigger-commit-butt",false);

                    } else{
                        document.getElementById("trigger-row1").className ="danger";
                        document.getElementById("trigger-row2").className ="danger";
                        disable_id("trigger-commit-butt",true);
                    }
            }
            if (response.device.status.channel_setup_complete == 0 && response.device.status.channel_trigger_complete == 0){
                disable_setup_4(true);
                document.getElementById("trigger-row1").className ="success";
                document.getElementById("trigger-row2").className ="success";
                document.getElementById("setup-4").className="panel panel-success"
                disable_setup_5(false);
                document.getElementById("setup-5").className="panel panel-danger"
                if (response.device.status.capture_settings_verify == 0){
                document.getElementById("capture-row").className ="success";
                disable_id("capture_butt",false)
                } else {
                    document.getElementById("capture-row").className ="danger";
                    disable_id("capture_butt",true)
                }
            }

            if (response.device.status.capture_settings_complete == 0){
                disable_setup_5(true);
                document.getElementById("setup-5").className="panel panel-success"

            }
    }
}

function disable_setup_1(bool){
    id_list = ["bit-mode-dropdown","connect_butt"]
    for (let x in id_list){
        document.getElementById(id_list[x]).disabled = bool;
    }
}

function disable_setup_2(bool){
    id_list = ["time-base-input","channel-checkboxes","commit_chan_active_butt"]
    for (let x in id_list){
        document.getElementById(id_list[x]).disabled = bool;
    }
}

function disable_setup_3(bool){
    disable_setup_3_chan("a",bool);
    disable_setup_3_chan("b",bool);
    disable_setup_3_chan("c",bool);
    disable_setup_3_chan("d",bool);
    disable_id("commit_chan_setting_butt",bool);
}
function disable_setup_3_chan(chan, bool){
    id_list = ['channel-'+chan+'-coupl','channel-'+chan+'-range','channel-'+chan+'-offset']
    for (let x in id_list){
        document.getElementById(id_list[x]).disabled = bool;
    }
}

function disable_setup_4(bool){
    id_list = ["trigger-enable","trigger-source","trigger-direction","trigger-threshold","trigger-delay","trigger-auto","trigger-commit-butt"]
    for (let x in id_list){
        document.getElementById(id_list[x]).disabled = bool;
    }
}

function disable_setup_5(bool){
    id_list = ["capture-pretrig-samples","capture-posttrig-samples","capture-count","capture_butt"]
    for (let x in id_list){
        document.getElementById(id_list[x]).disabled = bool;
    }
}

function disable_id(id,bool){
    document.getElementById(id).disabled = bool;
}


function set_channel_coupl(id,coupl){
    console.log("Pass");
}

function set_resolution(){
    var res = document.getElementById('bit-mode-dropdown').value;
    console.log(res)
    ajax_put('connection/','resolution',res)
}

function printinfo(id){
    console.log(document.getElementById(id).value)
}

function connect_to_picoscope(){
    var value = 0
    ajax_put('connection/','connect',value)
}

function complete_channels_defined(){
    var value = 0
    ajax_put('status/','pico_setup_complete',value)
}

function complete_channel_settings(){
    var value = 0
    ajax_put('status/','channel_setup_complete',value)
}

function complete_trigger_settings(){
    var value = 0
    ajax_put('status/','channel_trigger_complete',value)
}

function complete_capture_settings(){
    var value = 0
    ajax_put('status/','capture_settings_complete',value)
}

function verify_channel_settings(id, channel){
    var isfloat = (verify_float(id))
    var offset = (document.getElementById(id).value)
    if (isfloat == 1){
        ajax_put('settings/channels/'+channel+'/','verified',offset)
    } else {
        console.log("Input is not float")
    }
}
// Trigger commits

function commit_to_adapter(id,path,key){
    var value = document.getElementById(id).value
    if (value == "true"){ value = true}
    if (value == "false"){ value = false}
    ajax_put(path,key,value)
}

function commit_int_adapter(id,path,key){
    var input = parseInt(document.getElementById(id).value)
    console.log(input)
    if (isNaN(input)){
        console.log("Invalid")
    } else {
        console.log("Valid")
        ajax_put(path,key,input)
    }
}

function commit_timebase(id){
    var input_box = (document.getElementById(id))
    if (verify_int(id) === 1){
        console.log("Input good")
        ajax_put('settings/','timebase',parseInt(input_box.value))
    } else{
        ajax_put('settings/','timebase',null)
        console.log("Input bad >:[")
    }
    //var input_box = (document.getElementById(id));
}

function commit_channel_active(id, channel){
    var checked = document.getElementById(id).checked
    ajax_put('settings/channels/'+channel+'/','active',checked)
}

function commit_channel_coupling(id, channel){
    var coupling = document.getElementById(id).value
    ajax_put('settings/channels/'+channel+'/','coupling',coupling)
}

function commit_channel_range(id, channel){
    var range = document.getElementById(id).value
    ajax_put('settings/channels/'+channel+'/','range',range)    
}

function commit_channel_offset(id, channel){
    var offset = parseFloat(document.getElementById(id).value)
    console.log(offset)
    if (isNaN(offset)){
        console.log("Invalid")
    } else {
        console.log("Valid")
        ajax_put('settings/channels/'+channel+'/','offset',offset)
    }


    //ajax_put('settings/channels/'+channel+'/','offset',offset)
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
        return(('-'+testnum.toFixed(2))+' '+siUnit[i]+'A')
    } else{
        return((testnum.toFixed(2))+' '+siUnit[i]+'A')
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