function get_subtitle() {
    fetch(SERVER_URL + "/subtitle")
        .then(response => response.json())
        .then(data => {
            // Access the subtitle content from the response data
            const subtitleContent = data.content;
            document.getElementById("subtitle_input").textContent = subtitleContent;
            // Do something with the subtitle content
            // console.log(subtitleContent);
        })
        .catch(error => {
            // Handle any errors that occurred during the fetch request
            console.error(error);
        });
}

function post_subtitle() {
    var subtitleContent = document.getElementById("subtitle_input").value;
    fetch(SERVER_URL + "/subtitle", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content: subtitleContent })
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response from the server
        console.log(data);
        // Show success Sweet Alert
        Swal.fire({
          title: "Subtitle Saved",
          text: "Subtitle content has been successfully saved.",
          icon: "success",
          confirmButtonColor: "#3085d6",
          confirmButtonText: "OK"
        });
      })
      .catch(error => {
        // Handle any errors that occurred during the fetch request
        console.error(error);
        // Show error Sweet Alert
        Swal.fire({
          title: "Error",
          text: "Subtitle content could not be saved.",
          icon: "error",
          confirmButtonColor: "#3085d6",
          confirmButtonText: "OK"
        });
      });
  }
  
