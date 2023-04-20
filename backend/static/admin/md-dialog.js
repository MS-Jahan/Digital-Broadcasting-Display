function openDialog(dialogText) {
    document.getElementById("my-dialog-content").textContent = dialogText;
    var dialog = new mdc.dialog.MDCDialog(document.getElementsByClassName('mdc-dialog')[0]);

    // document.getElementById("dialog-cancel").addEventListener('click', (e) => {

    //     loadIframe("Online Class Credentials", document.location.href);
    // });
    var stat = "";
    dialog.open();

}

var dialog = new mdc.dialog.MDCDialog(document.getElementsByClassName('mdc-dialog')[0]);
