FROM nginx:1.27-alpine

# Copy the static site
COPY index.html /usr/share/nginx/html/index.html
COPY tick-delivery-report.html /usr/share/nginx/html/tick-delivery-report.html
COPY milestones /usr/share/nginx/html/milestones

# Cloud Run injects PORT; nginx must listen on $PORT
COPY nginx.conf /etc/nginx/templates/default.conf.template

ENV PORT=8080
EXPOSE 8080

# nginx:alpine entrypoint already renders templates from /etc/nginx/templates
CMD ["nginx", "-g", "daemon off;"]
