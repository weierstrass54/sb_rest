#!/bin/bash

echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/11/main/pg_hba.conf
echo "listen_addresses='*'" >> /var/lib/postgresql/11/main/postgresql.conf
pg_ctlcluster 11 main start

sudo -u postgres psql -c "CREATE USER sb_rest WITH ENCRYPTED PASSWORD 'sb_rest';"
sudo -u postgres createdb sb_rest

python main.py