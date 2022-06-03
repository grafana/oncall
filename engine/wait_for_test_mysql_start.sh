#!/usr/bin/env bash

until nc -z -v -w30 mysql_test 3306
do
    echo "Waiting for database connection..."
    sleep 1
done