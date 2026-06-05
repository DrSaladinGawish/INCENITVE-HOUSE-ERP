#!/bin/bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/ihe-erp.key \
    -out certs/ihe-erp.crt \
    -subj "/CN=IncentiveHouse ERP" \
    -addext "subjectAltName=DNS:localhost,DNS:incentivehouse.local"
echo "Certs generated in ./certs/"
echo "  - ihe-erp.crt"
echo "  - ihe-erp.key"
