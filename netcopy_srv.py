import socket
import hashlib
import sys
import os

CHUNK_SIZE = 4096
RECEIVE_TIMEOUT = 30.0

class FileTransferServer:
    #Server for receiving files with checksum validation.
    
    def __init__(self, bind_ip: str, bind_port: int, chsum_ip: str, chsum_port: int):
        #Initialize the file transfer server
        self.bind_ip = bind_ip
        self.bind_port = bind_port
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
    
    def receive_file(self, out_file: str) -> bool:
        """
        Receive a file from a client
        
        Args:
            out_file: Path where to save the received file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((self.bind_ip, self.bind_port))
                sock.listen(1)
                
                conn, addr = sock.accept()
                print(f"Connection from {addr}")
                
                with conn:
                    with open(out_file, 'wb') as f:
                        while True:
                            chunk = conn.recv(CHUNK_SIZE)
                            if not chunk:
                                break
                            f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"Error receiving file: {e}")
            return False
    
    def get_checksum(self, file_id: str) -> Optional[str]:
        """
        Retrieve checksum from the checksum server
        
        Args:
            file_id: Identifier for the file
            
        Returns:
            Optional[str]: Checksum if found, None otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.chsum_ip, self.chsum_port))
                
                msg = f"KI|{file_id}\n"
                sock.sendall(msg.encode())
                data = sock.recv(1024).decode()
            
            if "|" not in data:
                print(f"Invalid checksum server response: {data}")
                return None
            
            parts = data.split("|", 1)
            if len(parts) != 2:
                print(f"Invalid checksum server response format: {data}")
                return None
            
            length_str, checksum = parts
            try:
                length = int(length_str)
            except ValueError:
                print(f"Invalid length in checksum response: {length_str}")
                return None
            
            if length > 0:
                return checksum
            else:
                print("Checksum not found or expired")
                return None
                
        except Exception as e:
            print(f"Error retrieving checksum: {e}")
            return None
    
    def receive_and_validate(self, file_id: str, out_file: str) -> bool:
        """
        Receive a file and validate its checksum
        
        Args:
            file_id: Identifier for the file
            out_file: Path where to save the received file
            
        Returns:
            bool: True if successful and valid, False otherwise
        """
        try:
            # Receive file
            if not self.receive_file(out_file):
                return False
            
            # Get expected checksum
            expected_checksum = self.get_checksum(file_id)
            if expected_checksum is None:
                print("Could not retrieve expected checksum")
                return False
            
            # Calculate actual checksum
            actual_checksum = self.calculate_md5(out_file)
            
            # Compare checksums
            if expected_checksum == actual_checksum:
                print("CSUM OK")
                return True
            else:
                print("CSUM CORRUPTED")
                return False
                
        except Exception as e:
            print(f"Error in receive_and_validate: {e}")
            return False

def main():
    """Main function for file transfer server."""
    if len(sys.argv) != 7:
        print("Usage: python netcopy_srv.py <bind_ip> <bind_port> <chsum_ip> <chsum_port> <file_id> <out_file>")
        sys.exit(1)
    
    try:
        bind_ip, bind_port, chsum_ip, chsum_port, file_id, out_file = sys.argv[1:]
        
        # Validate output directory exists
        out_dir = os.path.dirname(out_file)
        if out_dir and not os.path.exists(out_dir):
            print(f"Error: Output directory does not exist: {out_dir}")
            sys.exit(1)
        
        server = FileTransferServer(bind_ip, int(bind_port), chsum_ip, int(chsum_port))
        
        if not server.receive_and_validate(file_id, out_file):
            print("File reception failed")
            sys.exit(1)
            
    except ValueError:
        print("Error: Port numbers must be valid integers")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 0:
        script_name = os.path.basename(sys.argv[0])
        if script_name == "checksum_srv.py":
            # Run checksum server
            main()  # This will call the checksum server main
        elif script_name == "netcopy_cli.py":
            # Run client
            main()  # This will call the client main
        elif script_name == "netcopy_srv.py":
            # Run file server
            main()  # This will call the file server main
        else:
            print("Please run individual components:")
            print("  python checksum_srv.py <ip> <port>")
            print("  python netcopy_cli.py <srv_ip> <srv_port> <chsum_ip> <chsum_port> <file_id> <file_path>")
            print("  python netcopy_srv.py <bind_ip> <bind_port> <chsum_ip> <chsum_port> <file_id> <out_file>")