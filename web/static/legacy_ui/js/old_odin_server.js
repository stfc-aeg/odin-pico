api_version = '0.1';
channels = []

settings_array = []
//runs when the script is loaded
$( document ).ready(function() {
    dis_all_channel_checkbox(true);
    disable_submit(true)

    // update_api_version();
    // update_api_adapters();
    // update_detected_devices();
    
});

//gets the most up to date api version
function update_api_version() {
    $.getJSON('/api', function(response) {
        $('#api-version').html(response.api);
        api_version = response.api;
    });
}

//obtains the current loaded api adapters
function update_api_adapters() {
    $.getJSON('/api/' + api_version + '/adapters/', function(response) {
        adapter_list = response.adapters.join(", ");
        $('#api-adapters').html(adapter_list);
    });
}

//interrogates the parameter tree to get the current list of connected GPIB devices
function update_detected_devices() {
    $.getJSON('/api/' + api_version + '/gpib/', function(response) {
        id_list = response.device_ids;

    }); 
}

function disable_submit(cond){
    document.getElementById("submit_settings").disabled = cond  
}

function read_selection(id){
    var value = document.getElementById(id).value
    console.log(value)
}

function reset_channels(){
    console.log("input is being modified")
    dis_all_channel_checkbox(true);
    //disable eventual submit button 
}

function dis_all_channel_checkbox(cond){
    document.getElementById("channel-a").disabled = cond
    document.getElementById("channel-b").disabled = cond
    document.getElementById("channel-c").disabled = cond
    document.getElementById("channel-d").disabled = cond
    document.getElementById("channel-a").checked = false
    document.getElementById("channel-b").checked = false
    document.getElementById("channel-c").checked = false
    document.getElementById("channel-d").checked = false
    $("#trig-chan-dropdown").empty();

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
    var regexCurr = /^[+-]?(?:\d*\.)?\d+$/;
    if (regexCurr.test(input_box.value)){
        return 1
    } else {
        input_box.value = "";
        return 0
    }       
}

function verify_channel_setup(){
    var v_o = verify_float('offset-input')
    var v_pre = verify_int('pre-trig-input')
    var v_post = verify_int('post-trig-input')
    var v_c = verify_int('captures-input')
    var v_t = verify_int('threshold-input')

    if (v_o && v_pre && v_post && v_c && v_t == 1){
        disable_submit(false);
    } else {
        disable_submit(true);
    }

}

function verify_timebase(id){
    var regexInt = /^\d+$/;
    var bitmode = document.getElementById('bit-mode-dropdown').value
    var inputbox = document.getElementById("time-base-input")
    var input_value = parseInt(inputbox.value)

    console.log(inputbox.value)
   

    if (regexInt.test(inputbox.value)){

        console.log("Input is number")
        var trigdrop = document.getElementById("trig-chan-dropdown")

        if (bitmode == "PS5000A_DR_12BIT"){
            if (parseInt(input_value) <1){
                console.log("Input is illegal and no channels active")   
            } else if (input_value == 1){
                console.log("Input is legal and one channels active")

                document.getElementById("channel-a").disabled = false;

                var opt1 = document.createElement('option')
                opt1.text = "Channel A"
                opt1.value = "PS5000A_CHANNEL_A"
                trigdrop.add(opt1,trigdrop[0])

            } else if (input_value == 2){
                console.log("Input is legal and two channels active")
                document.getElementById("channel-a").disabled = false;
                document.getElementById("channel-b").disabled = false;

                var opt1 = document.createElement('option')
                opt1.text = "Channel A"
                opt1.value = "PS5000A_CHANNEL_A"
                trigdrop.add(opt1,trigdrop[0])

                var opt2 = document.createElement('option')
                opt2.text = "Channel B"
                opt2.value = "PS5000A_CHANNEL_B"
                trigdrop.add(opt2,trigdrop[1])

            } else if (input_value >= 3){
                console.log("Input is legal and four channels active")
                dis_all_channel_checkbox(false);

                var opt1 = document.createElement('option')
                opt1.text = "Channel A"
                opt1.value = "PS5000A_CHANNEL_A"
                trigdrop.add(opt1,trigdrop[0])

                var opt2 = document.createElement('option')
                opt2.text = "Channel B"
                opt2.value = "PS5000A_CHANNEL_B"
                trigdrop.add(opt2,trigdrop[1])

                var opt3 = document.createElement('option')
                opt3.text = "Channel C"
                opt3.value = "PS5000A_CHANNEL_C"
                trigdrop.add(opt3,trigdrop[2])

                var opt4 = document.createElement('option')
                opt4.text = "Channel D"
                opt4.value = "PS5000A_CHANNEL_D"
                trigdrop.add(opt4,trigdrop[3])
            }
        } else if (bitmode == "PS5000A_DR_8BIT"){
            if (parseInt(input_value) <0){
                console.log("Input is illegal and no channels active")   
            } else if (input_value == 0){
                console.log("Input is legal and one channels active")
                document.getElementById("channel-a").disabled = false;

                var opt1 = document.createElement('option')
                opt1.text = "Channel A"
                opt1.value = "PS5000A_CHANNEL_A"
                trigdrop.add(opt1,trigdrop[0])

            } else if (input_value == 1){
                console.log("Input is legal and two channels active")
                document.getElementById("channel-a").disabled = false;
                document.getElementById("channel-b").disabled = false;

                var opt1 = document.createElement('option')
                opt1.text = "Channel A"
                opt1.value = "PS5000A_CHANNEL_A"
                trigdrop.add(opt1,trigdrop[0])

                var opt2 = document.createElement('option')
                opt2.text = "Channel B"
                opt2.value = "PS5000A_CHANNEL_B"
                trigdrop.add(opt2,trigdrop[1])

            } else if (input_value >= 2){
                console.log("Input is legal and four channels active")
            dis_all_channel_checkbox(false);

            var opt1 = document.createElement('option')
            opt1.text = "Channel A"
            opt1.value = "PS5000A_CHANNEL_A"
            trigdrop.add(opt1,trigdrop[0])

            var opt2 = document.createElement('option')
            opt2.text = "Channel B"
            opt2.value = "PS5000A_CHANNEL_B"
            trigdrop.add(opt2,trigdrop[1])

            var opt3 = document.createElement('option')
            opt3.text = "Channel C"
            opt3.value = "PS5000A_CHANNEL_C"
            trigdrop.add(opt3,trigdrop[2])

            var opt4 = document.createElement('option')
            opt4.text = "Channel D"
            opt4.value = "PS5000A_CHANNEL_D"
            trigdrop.add(opt4,trigdrop[3])
            }    
        }

    } else {
        inputbox.value = ""
        console.log("Input is either float or string")
    }
}

function submit_settings(){
    
}
// console.log(Number.isInteger(17));

// console.log(Math.ceil(16.00000001));


// $(".dropdown-menu li a").click(function(){
//     console.log(this)
//     $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
//     $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
//     console.log($(this).parents(".dropdown").find('.btn').val($(this).data('value')));
//   });

// function change_select(id){
//     //console.log(id)
//     $(id).parents(".dropdown").find('.btn').html($(id).text() + ' <span class="caret"></span>');
//     $(id).parents(".dropdown").find('.btn').val($(id).data('value'));
// }

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
        url: '/api/' + api_version + '/gpib/devices/' + path,
        //api_version + adapter_name_in_cfg/main_adapter_paramtree_path
        contentType: "application/json",
        data: JSON.stringify(data),
    });
}