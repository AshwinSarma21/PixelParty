# PixelParty
Pixel Party

## Inspiration
We've always wanted to have something to put in a room that not only could serve as a dynamic programmable display piece, but also one that lets us connect with friends at any distance. The PixelParty interactive LED matrix allows you and your friends to draw anything you want and see every digital brush stroke in real time on a physical panel. The PixelParty offers a way to make online interactions feel more physically present, and also a fun creative activity for friends hanging out in your room. 
## What it does
The PixelParty is a 64x64 pixel LED matrix that can be used as a canvas via the web interface. The web interface offers a pixelated canvas which you can use to draw anything on as well as a color selector for choosing any RGB color. Changes made to the canvas are reflected to all users in real time, as well as the physical LED panel. 
## How we built it
We used a Raspberry Pi 3 B+ with numerous GPIO pins connected to the IO pins of an Adafruit LED 64x64 matrix, which is additionally hooked up to a 5V 20A power supply. We used the rpi-led-matrix library by hzeller on github to control the LED matrix without the proprietary IO hat. We utilized a flask server which additionally launches a separate process it communicates with which manages the physical panel, all written in Python. Canvas interactions and updates are handled by JavaScript code served by the flask server. 
## Challenges we ran into 
A challenge was creating the backend as we needed to create a system that could handle multiple users contributing drawings concurrently without having issues with incorrectly displaying the canvas., that is, the physical display and the canvas displayed virtually on the website have to always match for all users in real time. We then had to learn the libraries that would display colors at each pixel on the matrix, which was more difficult as we had no special HAT; we had to spend a lot of time tweaking arguments in order to optimize and properly display images to the LED matrix with minimal processing power. 
## Accomplishments that we're proud of
For being our first hackathon project, we are very proud of all that we have managed to accomplish. We were able to successfully create a full stack web app with a functional front end support for many devices, create a backend that could process and sync multiple users’ inputs, set up and wire an adafruit LED matrix to run connected to a Raspberry Pi 3 B+ without any additional HAT and was able to accurately display the live canvas in real time through the web app, and lastly we were able to set the project to work from a domain on the internet. 
## What we learned
We learned about full-stack app development (HTML CSS JS Flask Python C++), IoT, Networking, Embedded Hardware and Software Integration. 
## What's next for PixelParty
Due to the nature of the hackathon, we were only able to create one device, however, we envision this being a device that anyone can have set up in their rooms each with their own distinct URL and canvas so that each owner can have them and their friends contribute to its respective canvas.
