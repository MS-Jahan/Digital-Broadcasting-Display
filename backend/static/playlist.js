function move_up(e) {
    console.log(e);
    try {
        current_list_element = e.closest("li");
        var previous_list_element = current_list_element.previousElementSibling;

        var current_index_data_id = current_list_element.getAttribute("data-item-id");
        var previous_index_data_id = previous_list_element.getAttribute("data-item-id");

        if (previous_list_element) {
            fetch(SERVER_URL + `/api/playlist_item/swap?one=${current_index_data_id}&another=${previous_index_data_id}`).then((response) => {
                console.log(response);
                get_playlist_items('playlist-ul');
            });
        }
    } catch (error) {
        console.log(error);
    }
}

function move_down(e) {
    console.log(e);
    try {
        current_list_element = e.closest("li");
        var next_list_element = current_list_element.nextElementSibling;

        var current_index_data_id = current_list_element.getAttribute("data-item-id");
        var next_index_data_id = next_list_element.getAttribute("data-item-id");

        if (next_list_element) {
            fetch(SERVER_URL + `/api/playlist_item/swap?one=${current_index_data_id}&another=${next_index_data_id}`).then((response) => {
                console.log(response);
                get_playlist_items('playlist-ul');
            });
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
                var item_id = current_list_element.getAttribute("data-item-id");
                deletePlaylistItem(item_id);
            }
        });
    } catch (error) {
        console.log(error);
    }
}

function deletePlaylistItem(itemId) {
    fetch(`/api/playlist_item/delete?id=${itemId}`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        Swal.fire(
            'Deleted!',
            data.message,
            'success'
        );
        get_playlist_items('playlist-ul');
    })
    .catch(error => {
        console.log(error);
        Swal.fire(
            'Error',
            'An error occurred while deleting the item.',
            'error'
        );
    });
}

function play_item_from_list(e) {
    console.log("play clicked")
    try {
        current_list_element = e.closest("li");
        item_id = Array.from(current_list_element.parentNode.querySelectorAll("li")).indexOf(current_list_element);
        admin_socket.emit('admin_play_item', { current_item_index: item_id });
    } catch (error) {
        console.log(error);
    }
}

function get_playlist_items(target) {
    fetch(SERVER_URL + "/api/playlist_items")
        .then(response => response.json())
        .then(data => {
            var ul = document.getElementById(target);
            var ul_innerhtml = "";

            data.items.forEach(function (item) {
                let content;
                if (item.type === 'video') {
                    content = `<i class="material-icons  mdl-list__item-avatar">movie</i> ${item.content}`;
                } else if (item.type === 'image') {
                    content = `<i class="material-icons  mdl-list__item-avatar">image</i> <img src="/uploads/images/${item.content}" width="50">`;
                } else {
                    content = `<i class="material-icons  mdl-list__item-avatar">title</i> ${item.content}`;
                }

                ul_innerhtml += `<li class="transition-c mdl-list__item" data-item-id="${item.id}" data-item-type="${item.type}">
                    <span class="mdl-list__item-primary-content" style="overflow-wrap: anywhere;">
                        ${content}
                    </span>
                    <span onclick="move_up(this)" class="mdl-list__item-secondary-action" style="margin-inline: 10px;">
                        <label class="mdl-button mdl-js-button mdl-button--icon"><i class="material-icons">arrow_upward</i></label>
                    </span>
                    <span onclick="move_down(this)" class="mdl-list__item-secondary-action" style="margin-inline: 10px;">
                        <label class="mdl-button mdl-js-button mdl-button--icon"><i class="material-icons">arrow_downward</i></label>
                    </span>
                    <span onclick="play_item_from_list(this)" class="mdl-list__item-secondary-action" style="margin-inline: 10px;">
                        <label class="mdl-button mdl-js-button mdl-button--icon"><i class="material-icons">play_arrow</i></label>
                    </span>
                    <span onclick="del(this)" class="mdl-list__item-secondary-action" style="margin-inline: 10px;">
                        <label class="mdl-button mdl-js-button mdl-button--icon"><i class="material-icons">close</i></label>
                    </span>
                </li>`;
            });
            ul.innerHTML = ul_innerhtml;
        });
}

document.getElementById('add-text-notice-button').addEventListener('click', function() {
    Swal.fire({
        title: 'Add Text Notice',
        html:
            '<input id="swal-input1" class="swal2-input" placeholder="Content">' +
            '<input id="swal-input2" class="swal2-input" placeholder="Duration (seconds)">' +
            '<input id="swal-input3" class="swal2-input" placeholder="Font Size (e.g., 24px)">' +
            '<input id="swal-input4" class="swal2-input" placeholder="Text Color (e.g., #FF0000)">' +
            '<input id="swal-input5" class="swal2-input" placeholder="Background Color (e.g., rgba(0,0,0,0.5))">',
        focusConfirm: false,
        preConfirm: () => {
            return [
                document.getElementById('swal-input1').value,
                document.getElementById('swal-input2').value,
                document.getElementById('swal-input3').value,
                document.getElementById('swal-input4').value,
                document.getElementById('swal-input5').value
            ]
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const [content, duration, font_size, text_color, bg_color] = result.value;
            fetch('/api/playlist_item/add_notice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, duration, font_size, text_color, bg_color })
            }).then(() => get_playlist_items('playlist-ul'));
        }
    });
});

document.getElementById('add-image-notice-button').addEventListener('click', function() {
    Swal.fire({
        title: 'Add Image Notice',
        html:
            '<input type="file" id="swal-input1" class="swal2-file">' +
            '<input id="swal-input2" class="swal2-input" placeholder="Duration (seconds)">',
        focusConfirm: false,
        preConfirm: () => {
            return [
                document.getElementById('swal-input1').files[0],
                document.getElementById('swal-input2').value
            ]
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const [image, duration] = result.value;
            const formData = new FormData();
            formData.append('image', image);
            formData.append('duration', duration);
            fetch('/api/playlist_item/add_image_notice', {
                method: 'POST',
                body: formData
            }).then(() => get_playlist_items('playlist-ul'));
        }
    });
});
