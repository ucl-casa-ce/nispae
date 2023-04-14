let images = [];
const imageContainer = document.getElementById("image-container");

const BROKER = "Address to Websocket -ws- MQTT Broker"; //change this
const TOPIC = "topic/to/subscribe"; //change this
const client = mqtt.connect(BROKER);

console.log('Connecting...');

client.on('connect', function () {
  if (!client.connected) { client.reconnect() }
  console.log('Connected');
  client.subscribe(TOPIC);
})

client.on('error', (error) => { console.log(error) });

client.on("message", function (topic, message) {
  let base64IMG = base64js.fromByteArray(message)
  const newImageSrc = 'data:image/webp;base64,' + base64IMG;
  updateImageContainer(newImageSrc);
});

function updateImageContainer(newImageSrc) {
  // Create new image element
  const newImage = document.createElement("img");
  newImage.src = newImageSrc;

  // Add new image to the images array
  images.push(newImage);

  // Add new image to the container
  imageContainer.appendChild(newImage);

  // Check if container width exceeds maximum width
  while (imageContainer.scrollWidth > imageContainer.offsetWidth) {
    // Remove first image from the container and the images array
    const removedImage = images.shift();
    imageContainer.removeChild(removedImage);
  }
}