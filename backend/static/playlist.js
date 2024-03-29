function move_up(e) {
    console.log(e);
    try {
        current_list_element = e.closest("li");
        // Get current list element's index
        var list_items = current_list_element.parentNode.querySelectorAll("li");
        var current_index = Array.from(list_items).indexOf(current_list_element);
        var previous_index = current_index - 1;
        previous_list_element = current_list_element.previousElementSibling;

        var current_index_data_id = current_list_element.getAttribute("data-video-id");
        var previous_index_data_id = previous_list_element.getAttribute("data-video-id");


        if (previous_list_element) {
            var video_status = previous_list_element.getAttribute("video-status");
            if (video_status !== "unlisted") {
                // send request to server to swap current_index with previous_index in the playlist
                fetch(SERVER_URL + `/playlist_index_swap?one=${current_index_data_id}&another=${previous_index_data_id}`).then((response) => {
                    console.log(response);
                });

                previous_list_element.style.transform = "translateY(" + current_list_element.offsetHeight + "px)";
                current_list_element.style.transform = "translateY(-" + previous_list_element.offsetHeight + "px)";
                setTimeout(function () {
                    previous_list_element.parentNode.insertBefore(current_list_element, previous_list_element);
                    previous_list_element.style.transform = "";
                    current_list_element.style.transform = "";
                }, 500); // Change the time as per your requirement
            }
        }
        console.log("move_up out");
    } catch (error) {
        console.log(error);
    }
}


function move_down(e) {
    console.log(e);
    try {
        current_list_element = e.closest("li");

        // Get current list element's index
        var list_items = current_list_element.parentNode.querySelectorAll("li");
        var current_index = Array.from(list_items).indexOf(current_list_element);
        var next_index = current_index + 1;
        next_list_element = current_list_element.nextElementSibling;

        var current_index_data_id = current_list_element.getAttribute("data-video-id");
        var next_index_data_id = next_list_element.getAttribute("data-video-id");

        if (next_list_element) {
            var video_status = next_list_element.getAttribute("video-status");
            if (video_status !== "unlisted") {
                // send request to server to swap current_index with previous_index in the playlist
                fetch(SERVER_URL + `/playlist_index_swap?one=${current_index_data_id}&another=${next_index_data_id}`).then((response) => {
                    console.log(response);
                });

                next_list_element.style.transform = "translateY(-" + current_list_element.offsetHeight + "px)";
                current_list_element.style.transform = "translateY(" + next_list_element.offsetHeight + "px)";
                setTimeout(function () {
                    next_list_element.parentNode.insertBefore(current_list_element, next_list_element.nextSibling);
                    next_list_element.style.transform = "";
                    current_list_element.style.transform = "";
                }, 500); // Change the time as per your requirement
            }
        }
    } catch (error) {
        console.log(error);
    }
}


function del(e) {
    try {
        Swal.fire({
            title: 'Are you sure?',
            text: 'Do you really want to delete?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                const current_list_element = e.closest("li");

                // Get current list element's index
                var list_items = current_list_element.parentNode.querySelectorAll("li");
                var current_index = Array.from(list_items).indexOf(current_list_element);

                var current_index_data_id = current_list_element.getAttribute("data-video-id");

                // Send the video ID to the server
                deleteVideo(current_index_data_id);
            }
        });
    } catch (error) {
        console.log(error);
    }
}

function deleteVideo(videoId) {
    // Make an AJAX request to the server
    fetch(`/delete_video?id=${videoId}`, {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            // Handle the server response
            Swal.fire(
                'Deleted!',
                data.message,
                'success'
            );
        })
        .catch(error => {
            console.log(error);
            Swal.fire(
                'Error',
                'An error occurred while deleting the video.',
                'error'
            );
        });
}


function play_from_list(e) {
    console.log("play clicked")
    try {
        current_list_element = e.closest("li");
        video_id = Array.from(current_list_element.parentNode.querySelectorAll("li")).indexOf(current_list_element);
        admin_socket.emit('next_video', { data: 'next_video', current_video_index: video_id-1});
    } catch (error) {
        console.log(error);
    }
}

function get_videos(target) {
    fetch(SERVER_URL + "/all_videos", {
        method: "GET"
    })
        .then(response => response.json())
        .then(data => {
            // iterate through data['videos']
            var ul = document.getElementById(target);
            var ul_innerhtml = "";

            if (target === 'videos-ul') {
                data['videos'].forEach(function (video, index) {
                    var videoId = Object.keys(video)[0];
                    var videoFilename = video[videoId];
                    ul_innerhtml += `<li video-status="listed" class="transition-c mdl-list__item" data-video-id="${videoId}" id="playlist-item-3">
                        <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;">
                            <i class="material-icons  mdl-list__item-avatar">person</i>
                            ${videoFilename}
                        </span>
                        <span onclick="play_from_list(this)" class="mdl-list__item-secondary-action"
                            style="margin-inline: 10px;">
                            <label class="mdl-button mdl-js-button mdl-button--icon">
                                <i class="material-icons">play_arrow</i>
                            </label>
                        </span>
                        <span onclick="del(this)" class="mdl-list__item-secondary-action"
                            style="margin-inline: 10px;">
                            <label class="mdl-button mdl-js-button mdl-button--icon">
                                <i class="material-icons">close</i>
                            </label>
                        </span>
                    </li>`;
                });

                data['unlisted_videos'].forEach(function (video, index) {
                    var videoId = Object.keys(video)[0];
                    var videoFilename = video[videoId];
                    ul_innerhtml += `<li video-status="unlisted" class="transition-c mdl-list__item" data-video-id="${videoId}" id="playlist-item-3">
                        <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;">
                            <i class="material-icons  mdl-list__item-avatar">person</i>
                            ${videoFilename}
                        </span>
                        <span class="mdl-list__item-secondary-action"
                            style="margin-inline: 10px;">
                            <label class="mdl-button mdl-js-button mdl-button--icon">
                                <i class="material-icons">play_arrow</i>
                            </label>
                        </span>
                        <span onclick="del(this)" class="mdl-list__item-secondary-action"
                            style="margin-inline: 10px;">
                            <label class="mdl-button mdl-js-button mdl-button--icon">
                                <i class="material-icons">close</i>
                            </label>
                        </span>
                    </li>`;
                });
            } else if (target === 'playlist-ul') {
                data['videos'].forEach(function (video, index) {
                    var videoId = Object.keys(video)[0];
                    var videoFilename = video[videoId];

                    ul_innerhtml += `<li video-status="listed" class="transition-c mdl-list__item" data-video-id="${videoId}" id="playlist-item-3">
                <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;">
                    <i class="material-icons  mdl-list__item-avatar">person</i>
                    ${videoFilename}
                </span>
                <span onclick="move_up(this)" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">arrow_upward</i>
                    </label>
                </span>
                <span onclick="move_down(this)" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">arrow_downward</i>
                    </label>
                </span>
                <span onclick="make_video_unlisted(this)" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">visibility_off</i>
                    </label>
                </span>
            </li>`;
                });

                data['unlisted_videos'].forEach(function (video, index) {
                    var videoId = Object.keys(video)[0];
                    var videoFilename = video[videoId];
                    ul_innerhtml += `<li video-status="unlisted" class="transition-c mdl-list__item" data-video-id="${videoId}" id="playlist-item-3">
                <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;filter: blur(3px);">
                    <i class="material-icons  mdl-list__item-avatar">person</i>
                    ${videoFilename}
                </span>
                <span style="filter: blur(3px);margin-inline: 10px;" class="mdl-list__item-secondary-action">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">arrow_upward</i>
                    </label>
                </span>
                <span style="filter: blur(3px);margin-inline: 10px;" class="mdl-list__item-secondary-action">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">arrow_downward</i>
                    </label>
                </span>
                <span onclick="make_video_listed(this)" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">visibility</i>
                    </label>
                </span>
            </li>`;
                });
            }

            ul.innerHTML = ul_innerhtml;
        })
}


function make_video_unlisted(e) {
    try {
        var current_list_element = e.closest("li");
        current_list_element.setAttribute("video-status", "unlisted");
        // Get current list element's index
        var list_items = current_list_element.parentNode.querySelectorAll("li");
        var current_index = Array.from(list_items).indexOf(current_list_element);

        var current_list_element_data_id = current_list_element.getAttribute("data-video-id");

        // Do something with video_id
        fetch(SERVER_URL + `/make_video_unlisted?id=${current_list_element_data_id}`).then((response) => {
            console.log(response);
        });

        // Make li's first three span elements blur and remove onclick attribute
        var spans = current_list_element.querySelectorAll("span");
        for (var i = 0; i < Math.min(3, spans.length); i++) {
            spans[i].style.filter = "blur(3px)";
            if (i > 0 && i < spans.length - 1) {
                spans[i].removeAttribute("onclick");
            }
        }
        spans[3].setAttribute("onclick", "make_video_listed(this)");
        spans[3].querySelector("i.material-icons").textContent = "visibility";


    } catch (error) {
        console.log(error);
    }
}

function make_video_listed(e) {
    try {
        var current_list_element = e.closest("li");
        current_list_element.setAttribute("video-status", "listed");
        // Get current list element's index
        var list_items = current_list_element.parentNode.querySelectorAll("li");
        var current_index = Array.from(list_items).indexOf(current_list_element);
        var current_index_data_id = current_list_element.getAttribute("data-video-id");

        // Do something with video_id
        fetch(SERVER_URL + `/make_video_listed?id=${current_index_data_id}`).then((response) => {
            console.log(response);
        });

        // Make li's first three span elements remove blur and re-add onclick attribute
        var spans = current_list_element.querySelectorAll("span");
        spans[0].style.filter = "";
        spans[1].setAttribute("onclick", "move_up(this)");
        spans[1].style.filter = "";
        spans[2].setAttribute("onclick", "move_down(this)");
        spans[2].style.filter = "";
        spans[3].setAttribute("onclick", "make_video_unlisted(this)");
        spans[3].querySelector("i.material-icons").textContent = "visibility_off";
    } catch (error) {
        console.log(error);
    }
}
