from flask import Flask, render_template, request, jsonify
import ipaddress
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize DB
def init_db():
    with sqlite3.connect("subnet_manager.db") as conn:
        cursor = conn.cursor()
        
        
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                pc_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # In the init_db() function, update the pcs table creation:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER,
                ip_address TEXT NOT NULL UNIQUE,
                subnet_cidr TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            )
        """)
        
        conn.commit()

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/subnet_assignment')
def subnet_assignment():
    return render_template('index.html')


def get_organizations_data():
    conn = sqlite3.connect('subnet_manager.db')  # Use your actual DB name
    cursor = conn.cursor()

    # Fetch organizations
    cursor.execute("SELECT id, name FROM organizations")
    organizations_raw = cursor.fetchall()

    orgs_data = []

    for org_id, org_name in organizations_raw:
        # Fetch PCs for each organization
        cursor.execute("SELECT ip_address, subnet_cidr FROM pcs WHERE org_id = ?", (org_id,))
        pcs = cursor.fetchall()

        subnet_groups = {}
        for ip_str, subnet_cidr in pcs:
            ip = ipaddress.ip_address(ip_str)
            cidr = int(subnet_cidr)
            # Get the network the IP belongs to
            network = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
            subnet_key = str(network)

            if subnet_key not in subnet_groups:
                # Calculate subnet details
                hosts = list(network.hosts())
                subnet_groups[subnet_key] = {
                    'subnet': subnet_key,
                    'network_address': str(network.network_address),
                    'broadcast_address': str(network.broadcast_address),
                    'first_usable': str(hosts[0]) if hosts else None,
                    'last_usable': str(hosts[-1]) if hosts else None,
                    'total_hosts': len(hosts),
                    'pcs': [],
                    'subnets': f"Subnet {len(subnet_groups) + 1}"
                }
            subnet_groups[subnet_key]['pcs'].append(ip_str)

        orgs_data.append({
            'name': org_name,
            'subnets': list(subnet_groups.values())
        })

    conn.close()
    return orgs_data

@app.route("/existing_organizations")
def show_existing_orgs():
    organizations = get_organizations_data()
    return render_template("existing_org.html", organizations=organizations)
#@app.route('/existing_organizations')
#def existing_organizations():
#    with sqlite3.connect("subnet_manager.db") as conn:
#        cursor = conn.cursor()
#        cursor.execute("SELECT id, name FROM organizations")
#        orgs = cursor.fetchall()
#
#        org_data = []
#
#        for org_id, name in orgs:
#            cursor.execute("SELECT subnet FROM subnets WHERE org_id=?", (org_id,))
#            subnets = cursor.fetchall()
#
#            subnet_list = []
#            for i, (subnet_str,) in enumerate(subnets, start=1):
#                net = ipaddress.IPv4Network(subnet_str, strict=False)
#                pcs = list(net.hosts())  # usable IPs
#                pc_list = [str(ip) for ip in pcs]
#
#                subnet_list.append({
#                    "subnet_label": f"Subnet {i}",
#                    "subnet": subnet_str,
#                    "pcs": pc_list
#                })
#
#            org_data.append({
#                "name": name,
#                "subnets": subnet_list
#            })
#
#    return render_template('existing_org.html', org_data=org_data)


@app.route("/register_org", methods=["POST"])
def register_org():
    data = request.get_json()
    org_name = data.get("org_name")
    pc_count = data.get("pc_count")

    if not org_name or pc_count is None:
        return jsonify({"error": "Organization name and PC count are required"}), 400

    try:
        with sqlite3.connect("subnet_manager.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO organizations (name, pc_count) VALUES (?, ?)", (org_name, pc_count))
            conn.commit()
        return jsonify({"message": f"Organization '{org_name}' registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Organization already exists"}), 400

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json()
        ip_address = data.get("ip_address")
        subnet_input = data.get("subnet_mask")  # This can be either mask or CIDR
        org_name = data.get("org_name")

        if not ip_address or not subnet_input or not org_name:
            return jsonify({"error": "Missing required fields"}), 400

        # Handle both CIDR and subnet mask formats
        try:
            # Check if input is CIDR (just a number)
            if subnet_input.isdigit():
                subnet_bits = int(subnet_input)
                if subnet_bits < 0 or subnet_bits > 32:
                    return jsonify({"error": "Invalid CIDR notation. Must be between 0 and 32"}), 400
            else:
                # Input is a subnet mask, calculate the CIDR
                subnet_bits = sum(bin(int(x)).count('1') for x in subnet_input.split('.'))

            # Create network with the calculated CIDR
            network = ipaddress.IPv4Network(f"{ip_address}/{subnet_bits}", strict=False)
            
            with sqlite3.connect("subnet_manager.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, pc_count FROM organizations WHERE name=?", (org_name,))
                org = cursor.fetchone()
                if not org:
                    return jsonify({"error": "Organization not found"}), 404

            org_id, pc_count = org
            network = ipaddress.IPv4Network(f"{ip_address}/{subnet_bits}", strict=False)
            
            # Get hosts per subnet based on the subnet bits
            hosts_per_subnet = 2 ** (32 - subnet_bits) - 2
            
            # Calculate required number of subnets
            required_subnets = (pc_count + hosts_per_subnet - 1) // hosts_per_subnet
            
            # Check if we have enough space for required subnets
            available_subnets = 2 ** (32 - subnet_bits)
            if required_subnets > available_subnets:
                return jsonify({"error": "Cannot create required number of subnets"}), 400
            
            # Calculate how many subnets we need
            pcs_remaining = pc_count
            subnets_used = []
            current_subnet = network
            
            while pcs_remaining > 0:
                usable_hosts = list(current_subnet.hosts())
                if not usable_hosts:  # Check if we have any usable hosts
                    return jsonify({"error": "No usable hosts available in subnet"}), 400
                    
                pcs_in_subnet = min(pcs_remaining, len(usable_hosts))
                
                # Store subnet information
                subnets_used.append({
                    'network': current_subnet,
                    'pcs_count': pcs_in_subnet,
                    'usable_hosts': usable_hosts[:pcs_in_subnet]
                })
                
                # Insert PCs for this subnet
                for i in range(pcs_in_subnet):
                    try:
                        cursor.execute(
                            "INSERT INTO pcs (org_id, ip_address, subnet_cidr) VALUES (?, ?, ?)",
                            (org_id, str(usable_hosts[i]), subnet_bits)
                        )
                    except sqlite3.IntegrityError:
                        return jsonify({"error": f"IP address {str(usable_hosts[i])} is already in use"}), 400
                
                pcs_remaining -= pcs_in_subnet
                if pcs_remaining > 0:
                    next_network = int(current_subnet.network_address) + current_subnet.num_addresses
                    current_subnet = ipaddress.IPv4Network(
                        f"{ipaddress.IPv4Address(next_network)}/{subnet_bits}",
                        strict=False
                    )
            
            conn.commit()

            # Prepare response with subnet information
            subnet_info = [{
                'subnet': str(s['network']),
                'network_address': str(s['network'].network_address),
                'broadcast_address': str(s['network'].broadcast_address),
                'first_usable': str(s['network'].network_address+1),
                'last_usable': str(s['network'].broadcast_address-1),
                'pcs_allocated': s['pcs_count']
            } for s in subnets_used]

            response = {
                "network_address": str(network.network_address),
                "broadcast_address": str(network.broadcast_address),
                "total_hosts": network.num_addresses - 2,
                "organization": org_name,
                "assigned_subnet": str(network),
                "subnets": subnet_info
            }

            return jsonify(response)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/export_subnets", methods=["GET"])
def export_subnets():
    with sqlite3.connect("subnet_manager.db") as conn:
        cursor = conn.cursor()
        # Get all organizations
        cursor.execute("SELECT id, name FROM organizations")
        orgs = cursor.fetchall()
        
        result = []
        for org_id, org_name in orgs:
            # Get unique subnets for each organization by grouping PCs by subnet_cidr
            cursor.execute("""
                SELECT DISTINCT subnet_cidr, COUNT(*) as pc_count
                FROM pcs 
                WHERE org_id = ? 
                GROUP BY subnet_cidr
            """, (org_id,))
            subnets_data = cursor.fetchall()
            
            result.append({
                "organization": org_name,
                "subnet_count": len(subnets_data),
                "subnets": [{
                    "cidr": subnet_cidr,
                    "pc_count": count
                } for subnet_cidr, count in subnets_data]
            })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
