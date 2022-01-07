const delete_button = document.getElementById('delete_button');
delete_button.onclick = function (e) {
    const venue_id = e.target.dataset['id'];
    fetch('/venues/' + venue_id, {
        method: "DELETE"
    })
    .then(function() {
        window.location.href = '/venues';
    })
    .catch(function(e) {
        console.log('error', e)
    })
}
