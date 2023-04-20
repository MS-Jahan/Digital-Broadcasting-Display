// Navigation Drawer

const drawer = mdc.drawer.MDCDrawer.attachTo(document.querySelector('.mdc-drawer'));
const topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(document.getElementById('app-bar'));

topAppBar.setScrollTarget(document.getElementById('main-content'));
topAppBar.listen('MDCTopAppBar:nav', () => {
  drawer.open = !drawer.open;
});

// window.addEventListener("load", function(event) {
//    if(window.innerWidth > 1024) {
//       drawer.open = !drawer.open;
//    }
// });

const elements = document.getElementsByClassName('mdc-list-item');

 for (var i = 0; i < elements.length; i++) {
   elements[i].addEventListener('click', () => { drawer.open = !drawer.open; });
}