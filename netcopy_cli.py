import socket
import hashlib
import sys
import os
from pathlib import Path

CHUNK_SIZE = 4096
CHECKSUM_EXPIRY = 60

class FileTransferClient:

    #Client for transferring files with checksum validation.

    def __init__(self, srv_ip: str, srv_port: int, chsum_ip: str, chsum_port: int):
        #Initialize the file transfer client
        self.srv_ip = srv_ip
        self.srv_port = srv_port
        self.chsum_ip = chsum_ip
        self.chsum_port = chsum_port
    
    def calculate_md5(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MD5 hash as hexadecimal string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        md5_hash = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    md5_hash.update(chunk)
        except IOError as e:
            raise IOError(f"Error reading file {file_path}: {e}")
        
        return md5_hash.hexdigest()
    
    def send_file(self, file_path: str) -> bool:
        """
        Send file to the server
        
        Args:
            file_path: Path to the file to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.srv_ip, self.srv_port))
                
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        sock.sendall(chunk)
            
            return True
            
        except Exception as e:
            print(f"Error sending file: {e}")
            return False
    
    def send_checksum(self, file_id: str, checksum: str) -> bool:
        """
        Send checksum to the checksum server.
        
        Args:
            file_id: Identifier for the file
            checksum: MD5 checksum of the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.chsum_ip, self.chsum_port))
                
                msg = f"BE|{file_id}|{CHECKSUM_EXPIRY}|{len(checksum)}|{checksum}\n"
                sock.sendall(msg.encode())
                
                response = sock.recv(1024)
                if response != b"OK":
                    print(f"Warning: Unexpected checksum server response: {response}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error sending checksum: {e}")
            return False
    
    def transfer_file(self, file_id: str, file_path: str) -> bool:
        """
        Transfer a file including checksum validation
        
        Args:
            file_id: Identifier for the file
            file_path: Path to the file to transfer
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate checksum first
            checksum = self.calculate_md5(file_path)
            
            # Send file
            if not self.send_file(file_path):
                return False
            
            # Send checksum
            if not self.send_checksum(file_id, checksum):
                return False
            
            print(f"File {file_path} transferred successfully with ID {file_id}")
            return True
            
        except Exception as e:
            print(f"Error transferring file: {e}")
            return False

def main():
    #Main function for file transfer client
    if len(sys.argv) != 7:
        print("Usage: python netcopy_cli.py <srv_ip> <srv_port> <chsum_ip> <chsum_port> <file_id> <file_path>")
        sys.exit(1)
    
    try:
        srv_ip, srv_port, chsum_ip, chsum_port, file_id, file_path = sys.argv[1:]
        
        # Validate file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        client = FileTransferClient(srv_ip, int(srv_port), chsum_ip, int(chsum_port))
        
        if not client.transfer_file(file_id, file_path):
            print("File transfer failed")
            sys.exit(1)
            
    except ValueError:
        print("Error: Port numbers must be valid integers")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)