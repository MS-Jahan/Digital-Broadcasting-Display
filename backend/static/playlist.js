function move_up(e) {
    try {
        current_list_element = e.closest("li");
        previous_list_element = current_list_element.previousElementSibling;
        if (previous_list_element) {
            previous_list_element.style.transform = "translateY(" + current_list_element.offsetHeight + "px)";
            current_list_element.style.transform = "translateY(-" + previous_list_element.offsetHeight + "px)";
            setTimeout(function() {
                previous_list_element.parentNode.insertBefore(current_list_element, previous_list_element);
                previous_list_element.style.transform = "";
                current_list_element.style.transform = "";
            }, 500); // Change the time as per your requirement
        }
    } catch (error) {
        console.log(error);
    }
}

function move_down(e) {
    try {
        current_list_element = e.closest("li");
        next_list_element = current_list_element.nextElementSibling;
        if (next_list_element) {
            next_list_element.style.transform = "translateY(-" + current_list_element.offsetHeight + "px)";
            current_list_element.style.transform = "translateY(" + next_list_element.offsetHeight + "px)";
            setTimeout(function() {
                next_list_element.parentNode.insertBefore(current_list_element, next_list_element.nextSibling);
                next_list_element.style.transform = "";
                current_list_element.style.transform = "";
            }, 500); // Change the time as per your requirement
        }
    } catch (error) {
        console.log(error);
    }
}

function del(e){
    try {
        current_list_element = e.closest("li");
        current_list_element.remove();
    } catch (error) {
        console.log(error);
    }
}

function play(e){
    try {
        current_list_element = e.closest("li");
        video_id = current_list_element.getAttribute("data-video-id");
        // Do something with video_id
    } catch (error) {
        console.log(error);
    }
}