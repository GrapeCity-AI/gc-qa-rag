# Use the official Nginx image as the base image
FROM nginx:alpine

# Copy the custom Nginx configuration file to the default location in the container
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Copy the local dist directory to the /usr/share/nginx/html directory in the container
COPY ./dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx. The default CMD is already set to start Nginx, so no need to specify it here