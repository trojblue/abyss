// Create an IntersectionObserver
var observer = new IntersectionObserver(onIntersection, {rootMargin: "0px 0px 200px 0px"});

// Get all the image elements & observe each one; not including modal
var images = Array.from(document.getElementsByClassName("img-responsive")).filter(img => img.id != "ModalImage");

for (var i = 0; i < images.length; i++) {
    observer.observe(images[i]);
}

function onIntersection(entries) {
    // Loop through the entries
    for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];
        // If the image is intersecting the viewport and the id is not "ModalImage"
        if (entry.isIntersecting && entry.target.id !== "ModalImage") {
            console.log("INTERSECTY")
            // Load the image
            var img = entry.target;
            img.src = img.dataset.src;
            // Stop observing the image
            observer.unobserve(img);
        }
    }
}
