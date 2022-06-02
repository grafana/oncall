#!/bin/bash

export DJANGO_SETTINGS_MODULE=settings.all_in_one

generate_value_if_not_exist ()
{
  if [ ! -f /etc/app/secret_data/$1 ]; then
    touch /etc/app/secret_data/$1
    base64 /dev/urandom | head -c $2 > /etc/app/secret_data/$1
fi
export $1=$(cat /etc/app/secret_data/$1)
}

generate_value_if_not_exist SECRET_KEY 75

generate_value_if_not_exist MIRAGE_SECRET_KEY 75
generate_value_if_not_exist MIRAGE_CIPHER_IV 16

export BASE_URL=http://localhost:8000

echo "Starting redis in the background"
# Redis will dump the changes to the volume every 60 seconds if at least 1 key changed
redis-server --daemonize yes --save 60 1 --dir /etc/app/redis_data/
echo "Running migrations"
python manage.py migrate

echo "Start celery"
python manage.py start_celery &

# Postponing token issuing to make sure it's the last record in the console.
bash -c 'sleep 10; python manage.py issue_invite_for_the_frontend --override' &

echo "Starting server"
python manage.py runserver 0.0.0.0:8000 --noreload
