#!/usr/bin/env python3

import json
import logging
from math import inf
import os
import socketserver
import sys
import time
from logging.handlers import RotatingFileHandler
from setproctitle import setproctitle


class ForkingTCPRequestHandler(socketserver.BaseRequestHandler):
    def log(self, msg):
        remote_ip = self.client_address[0]
        if not remote_ip == '127.0.0.1':
            logging.info(f"{remote_ip}::{msg}")

    def send_msg(self, msg):
        jsonified = (json.dumps(msg) + '\n').encode()
        try:
            self.request.sendall(jsonified)
        except BrokenPipeError:
            pass

    def handle(self):
        self.log("connected")

        # Runs safely inside its own isolated OS process now!
        c = Challenge()
        max_recv_size = 1024
        if hasattr(c, 'max_payload_size'):
            max_recv_size = c.max_payload_size
        if hasattr(c, 'timeout_secs'):
            time_started = time.time()

        while True:
            if hasattr(c, 'before_input'):
                try:
                    self.request.sendall(c.before_input.encode())
                except BrokenPipeError:
                    break
                del c.before_input

            if hasattr(c, 'no_prompt'):
                del c.no_prompt
                datas = b"\n"
            else:
                # join fragmented packets
                if hasattr(c, 'max_payload_size'):
                    try:
                        buffer = b""
                        while len(buffer) < max_recv_size:
                            chunk = self.request.recv(1024)
                            if not chunk:
                                break
                            buffer += chunk
                            if b"\n" in chunk:
                                break
                    except ConnectionResetError:
                        break
                else:
                    try:
                        buffer = self.request.recv(max_recv_size)
                    except ConnectionResetError:
                        break

                if len(buffer) >= max_recv_size:
                    msg = {"error": f"You may send up to {max_recv_size} bytes per message. \n Your current meessage is of {len(buffer)} bytes!"}
                    self.send_msg(msg)
                    break

                if buffer:
                    self.log(buffer)

                if hasattr(c, 'timeout_secs') and time.time() > time_started + c.timeout_secs:
                    msg = {"error": f"Out of time"}
                    self.send_msg(msg)
                    break

                try:
                    datas = list(map(json.loads, buffer.strip().split(b"\n")))
                except json.decoder.JSONDecodeError as e:
                    if b"'" in buffer:
                        msg = {"error": "Invalid JSON. Remember to surround strings with double quotes rather than single quotes."}
                    else:
                        msg = {"error": "Invalid JSON"}
                    self.send_msg(msg)
                    break

            try:
                for data in datas:
                    out = c.challenge(data)
                    if hasattr(c, 'before_send'):
                        self.request.sendall(c.before_send.encode())
                        del c.before_send
                    if isinstance(out, list):
                        for obj in out:
                            self.send_msg(obj)
                    elif out is None:
                        pass
                    else:
                        self.send_msg(out)
                    if hasattr(c, 'exit'):
                        break
                if hasattr(c, 'exit'):
                    break
            except Exception as e:
                error = getattr(e, 'message', repr(e))
                msg = {"error": "Exception thrown", "exception": error}
                self.send_msg(msg)
                self.log(error)
                break


# Changed from ThreadingMixIn to ForkingMixIn
class ForkingTCPServer(socketserver.ForkingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    # Clean up zombie processes automatically
    max_children = 75


def start_server(port=0):
    setproctitle(f"netcat {port}")
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logging.basicConfig(
        handlers=[RotatingFileHandler(f'logs/{port}.log', maxBytes=50000000, backupCount=1)],
        level=logging.INFO,
        format=f'%(asctime)s::{port}::%(message)s',
    )
    with ForkingTCPServer(('0.0.0.0', port), ForkingTCPRequestHandler) as server:
        logging.info(f"Starting up on port {port} (Forking Mode)")
        
        # serve_forever can run directly in the main thread now, 
        # since ForkingTCPServer handles connections asynchronously via processes.
        server.serve_forever()
