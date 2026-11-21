# /etc/nginx/stackpilot-proxy.inc — shared proxy headers for StackPilot.
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Frappe-Site-Name hub.3-131-57-88.sslip.io;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-Real-IP $remote_addr;
proxy_read_timeout 180s;
