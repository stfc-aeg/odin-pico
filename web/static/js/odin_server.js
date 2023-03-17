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
            $("#bit-mode-dropdown").val(response.device.settings.resolution)
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
    }
}

function disable_id(id,bool){
    document.getElementById(id).disabled = bool;
}

function run_pico_command(){
    var value = 0
    ajax_put('commands/','run_capture',value)
}




function commit_to_adapter(id,path,key){
    var value = document.getElementById(id).value
    if (value == "true"){ value = true}
    if (value == "false"){ value = false}
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