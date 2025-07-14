import socket
import select
import time
import sys
import logging
from typing import Dict, Tuple, Optional

DEFAULT_BUFFER_SIZE = 1024
SELECT_TIMEOUT = 1.0

ChecksumStore = Dict[str, Tuple[float, str]]

class ChecksumServer:
    
    def __init__(self, ip: str, port: int):
        #Initialize the checksum server
        self.ip = ip
        self.port = port
        self.checksums_store: ChecksumStore = {}
        self.socket = None
        self.inputs = []
        self.connections = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def process_data(self, data: str) -> bytes:
        """
        Process incoming commands and return appropriate responses
        
        Commands:
        - BE|file_id|expiry|length|checksum: Store checksum with expiry
        - KI|file_id: Retrieve checksum if not expired
        
        Returns:
            bytes: Response data (OK, checksum data, or ERR)
        """
        try:
            parts = data.strip().split("|")
            if not parts:
                return b"ERR"

            command = parts[0]
            
            if command == "BE" and len(parts) == 5:
                return self._handle_store_command(parts)
            elif command == "KI" and len(parts) == 2:
                return self._handle_retrieve_command(parts)
            else:
                self.logger.warning(f"Invalid command format: {data}")
                return b"ERR"
                
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            return b"ERR"
    
    def _handle_store_command(self, parts: list) -> bytes:
        #Handle BE (store) command
        try:
            _, file_id, expiry, length, checksum = parts
            expiry_time = time.time() + int(expiry)
            self.checksums_store[file_id] = (expiry_time, checksum)
            self.logger.info(f"Stored checksum for file_id: {file_id}")
            return b"OK"
        except ValueError as e:
            self.logger.error(f"Invalid store command parameters: {e}")
            return b"ERR"
    
    def _handle_retrieve_command(self, parts: list) -> bytes:
        #Handle KI (retrieve) command
        _, file_id = parts
        entry = self.checksums_store.get(file_id)
        
        if not entry:
            return b"0|"
        
        expiry_time, checksum = entry
        if time.time() > expiry_time:
            self.checksums_store.pop(file_id, None)
            self.logger.info(f"Expired checksum removed for file_id: {file_id}")
            return b"0|"
        else:
            return f"{len(checksum)}|{checksum}".encode()
    
    def start(self):
        #Start the checksum server
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ip, self.port))
            self.socket.listen()
            
            self.inputs = [self.socket]
            self.logger.info(f"Checksum server running on {self.ip}:{self.port}")
            
            self._run_server_loop()
            
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self._cleanup()
    
    def _run_server_loop(self):
        #Main server loop handling connections
        while True:
            try:
                readable, _, _ = select.select(self.inputs, [], [], SELECT_TIMEOUT)
                for sock in readable:
                    if sock is self.socket:
                        self._handle_new_connection()
                    else:
                        self._handle_client_data(sock)
            except KeyboardInterrupt:
                self.logger.info("Server shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Server loop error: {e}")
    
    def _handle_new_connection(self):
        #Handle new client connections
        try:
            conn, addr = self.socket.accept()
            self.inputs.append(conn)
            self.connections[conn] = b""
            self.logger.info(f"New connection from {addr}")
        except Exception as e:
            self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_client_data(self, sock):
        #Handle data from existing client connections
        try:
            data = sock.recv(DEFAULT_BUFFER_SIZE)
            if data:
                self.connections[sock] += data
                if b"\n" in self.connections[sock]:
                    lines = self.connections[sock].split(b"\n")
                    for line in lines[:-1]:
                        response = self.process_data(line.decode())
                        sock.sendall(response)
                    self.connections[sock] = lines[-1]
            else:
                self._close_connection(sock)
        except Exception as e:
            self.logger.error(f"Error handling client data: {e}")
            self._close_connection(sock)
    
    def _close_connection(self, sock):
        #Close a client connection and clean up resources
        try:
            self.inputs.remove(sock)
            self.connections.pop(sock, None)
            sock.close()
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
    
    def _cleanup(self):
        #Clean up server resources
        for sock in self.inputs:
            try:
                sock.close()
            except:
                pass
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

def main():
    #Main function for checksum server
    if len(sys.argv) != 3:
        print("Usage: python checksum_srv.py <ip> <port>")
        sys.exit(1)
    
    try:
        ip, port = sys.argv[1], int(sys.argv[2])
        server = ChecksumServer(ip, port)
        server.start()
    except ValueError:
        print("Error: Port must be a valid integer")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()