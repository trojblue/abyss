// Create an IntersectionObserver
var observer = new IntersectionObserver(onIntersection, {rootMargin: "0px 0px 1000px 0px"});

// Get all the image elements & observe each one
var images = document.getElementsByClassName("img-responsive");

for (var i = 0; i < images.length; i++) {
    observer.observe(images[i]);
}

function onIntersection(entries) {
    // Loop through the entries
    for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];
        // If the image is intersecting the viewport
        if (entry.isIntersecting) {
            // Load the image
            var img = entry.target;
            img.src = img.dataset.src;
            // Stop observing the image
            observer.unobserve(img);
        }
    }
}