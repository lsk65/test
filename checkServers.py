import paramiko
from concurrent.futures import ThreadPoolExecutor

# Define the list of servers and the username
servers = [
    {"hostname": "192.168.1.1", "username": "user1"},
    {"hostname": "192.168.1.2", "username": "user2"},
    {"hostname": "192.168.1.3", "username": "user3"},
]

# Path to your private SSH key
private_key_path = "/path/to/your/private/key"  # Update the path accordingly

# Function to attempt SSH login
def attempt_ssh_login(server):
    hostname = server["hostname"]
    username = server["username"]
    
    try:
        # Load the private key
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, pkey=private_key, timeout=5)
        client.close()
        return hostname, True  # Success
    except paramiko.AuthenticationException:
        return hostname, False  # Failed authentication
    except Exception as e:
        return hostname, f"Error: {e}"  # Other errors

# Main function to iterate over servers and report results
def main():
    failed_attempts = []
    
    with ThreadPoolExecutor() as executor:
        results = executor.map(attempt_ssh_login, servers)

    for result in results:
        hostname, success = result
        if not success is True:
            failed_attempts.append((hostname, success))

    if failed_attempts:
        print("Failed SSH login attempts:")
        for hostname, outcome in failed_attempts:
            print(f"{hostname}: {outcome}")
    else:
        print("All SSH login attempts were successful.")

if __name__ == "__main__":
    main()
