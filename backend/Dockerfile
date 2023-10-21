FROM ubuntu:18.04
RUN apt-get update
# Set the home directory to /root
ENV HOME /pt1
# cd into the home directory
WORKDIR /pt1
# Install Node
RUN apt-get update --fix-missing
RUN apt-get install -y nodejs
RUN apt-get install -y npm
# Copy all app files into the image
COPY . .
# Download dependancies
RUN npm install
# Allow port 8080 to be accessed
# from outside the container
EXPOSE 3000
# Run the app
CMD node app.js
