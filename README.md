wdcnz-2012-site
===============

A Cassandra Twitter clone for WDCNZ 2012 - Wellington

Requirements
============

Python 2.7 with `virtualenv` and `easy_install`.

Setup
=====

Start a local Cassandra instance. 

Use `cassandra-cli` to create the schema with `cassandra-schema.txt`.

Create a Python virtual environment:

    ./boostrap-dev-env
    
Activate the environment:

    source .env/bin/activate

Start the server:

    ./start.py

Start a local Redis server.

In a new shell, activate the `.env` again and start celery.

    ./start-celery.sh 

