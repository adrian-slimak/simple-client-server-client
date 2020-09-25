# Simple remote device access

## Description:

A simple program that allows to perform basic functions from a local computer on a remote computer.
Communication takes place through an additional server.

These basic functions are:
- file transfer
- downloading files and entire folders
- file deletion
- launch of applications
- creating new folders
- listing information about files in a given location ('ls' function like)

## How to run

First, set the appropriate server ip address in *"local_client.py"* and *"remote_client.py"*.

Then, simply run the following files on the appropriate devices (the order of launch is irrelevant):

* "local_client.py" - run on local device (functions are executed from this device)
* "server.py" - run on server device (enables communication between clients and synchronization of the transmitted messages)
* "remote_elient.py" - run on remote device (functions are executed on this device)

All scripts can also be run on a single device.

## How it works:

This program uses python *sockets*.
Messages sent from a local client are added to the queue on the server.
If remote client is connected to the server, these messages are then send to remote client and executed (messages contains functions).
Once remote client completes its tasks, it sends a return message with the result back to the server and the to local client.
