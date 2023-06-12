function move_up(e) {
    try {
        current_list_element = e.closest("li");
        // Get current list element's index
        var list_items = current_list_element.parentNode.querySelectorAll("li");
        var current_index = Array.from(list_items).indexOf(current_list_element);
        var previous_index = current_index - 1;

        previous_list_element = current_list_element.previousElementSibling;
        if (previous_list_element) {
            var video_status = previous_list_element.getAttribute("video-status");
            if (video_status !== "unlisted") {
                // send request to server to swap current_index with previous_index in the playlist
                fetch(SERVER_URL + `/playlist_index_swap?one=${current_index}&another=${previous_index}`).then((response) => {
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
    } catch (error) {
        console.log(error);
    }
}


function move_down(e) {
    try {
        current_list_element = e.closest("li");

        // Get current list element's index
        var list_items = current_list_element.parentNode.querySelectorAll("li");
        var current_index = Array.from(list_items).indexOf(current_list_element);
        var next_index = current_index + 1;

        next_list_element = current_list_element.nextElementSibling;
        if (next_list_element) {
            var video_status = next_list_element.getAttribute("video-status");
            if (video_status !== "unlisted") {
                // send request to server to swap current_index with previous_index in the playlist
                fetch(SERVER_URL + `/playlist_index_swap?one=${current_index}&another=${next_index}`).then((response) => {
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
        current_list_element = e.closest("li");
        current_list_element.remove();
    } catch (error) {
        console.log(error);
    }
}

function play(e) {
    try {
        current_list_element = e.closest("li");
        video_id = current_list_element.getAttribute("data-video-id");
        // Do something with video_id
    } catch (error) {
        console.log(error);
    }
}

function get_all_video_list() {
    fetch(SERVER_URL + "/all_videos")
        .then(response => response.json())
        .then(data => {
            // iterate through data['videos']
            var playlist_ul = document.getElementById("playlist-ul");
            var playlist_ul_innerhtml = "";

            data['videos'].forEach(function (video_name, index) {
                playlist_ul_innerhtml += `<li video-status="listed" class="transition-c mdl-list__item" data-video-id="${index + 1}" id="playlist-item-3">
                <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;">
                    <i class="material-icons  mdl-list__item-avatar">person</i>
                    ${video_name}
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
                <span onclick="del(this)" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">close</i>
                    </label>
                </span>
            </li>`;
            });

            data['unlisted_videos'].forEach(function (video_name, index) {
                playlist_ul_innerhtml += `<li video-status="unlisted" class="transition-c mdl-list__item" data-video-id="${index + 1}" id="playlist-item-3">
                <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;filter: blur(3px);">
                    <i class="material-icons  mdl-list__item-avatar">person</i>
                    ${video_name}
                </span>
                <span style="filter: blur(3px);" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">arrow_upward</i>
                    </label>
                </span>
                <span style="filter: blur(3px);" class="mdl-list__item-secondary-action"
                    style="margin-inline: 10px;">
                    <label class="mdl-button mdl-js-button mdl-button--icon">
                        <i class="material-icons">arrow_downward</i>
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
            playlist_ul.innerHTML = playlist_ul_innerhtml;

        })
}

function make_video_unlisted(e) {
    try {
      var current_list_element = e.closest("li");
      // Get current list element's index
      var list_items = current_list_element.parentNode.querySelectorAll("li");
      var current_index = Array.from(list_items).indexOf(current_list_element);
  
      // Do something with video_id
      fetch(SERVER_URL + `/make_video_unlisted?id=${current_index}`).then((response) => {
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
    } catch (error) {
      console.log(error);
    }
  }
  