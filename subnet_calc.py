import ipaddress

def calculate_subnet(ip_address, subnet_mask):
    try:
        network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)
        return {
            "network_address": str(network.network_address),
            "broadcast_address": str(network.broadcast_address),
            "total_hosts": network.num_addresses,
            "usable_hosts": max(network.num_addresses - 2, 0),  # Excluding network & broadcast
            "first_usable_ip": str(network.network_address + 1) if network.num_addresses > 2 else "N/A",
            "last_usable_ip": str(network.broadcast_address - 1) if network.num_addresses > 2 else "N/A",
        }
    except ValueError:
        raise ValueError("Invalid IP address or subnet mask")
