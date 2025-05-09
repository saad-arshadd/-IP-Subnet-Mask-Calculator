# 🧮 IP Subnet Mask Calculator

A full-stack web application built for the **Computer Networks** course as a Final Year Project. This tool allows users to register organizations, input device requirements and base IP information, and automatically perform subnet calculations. It also visualizes subnet distribution using bar charts and allows users to export the subnet data.

---

## ✅ Features

- Register multiple organizations with device needs
- Automatically calculate:
  - Network Address
  - Broadcast Address
  - First & Last Usable IPs
  - Total Hosts & Required Hosts
  - Assigned Subnet Mask
- Subnet allocation and visualization using Chart.js
- Export subnet details in JSON format
- Responsive user interface using HTML, CSS, and JavaScript
- Backend logic implemented using Python (Flask)
- SQLite database for persistent storage

---

## 💻 Tech Stack

| Layer      | Technology        |
|------------|-------------------|
| Frontend   | HTML, CSS, JavaScript |
| Backend    | Python (Flask)    |
| Database   | SQLite            |
| Charting   | Chart.js          |

---

## 📁 Project Structure
ip_calculator/
│
├── app.py # Main Flask application (routing + backend logic)
├── subnet_calc.py # Core subnetting logic (network/broadcast calculations)
├── database.db # SQLite DB file
│
├── static/ # Static assets
│ ├── style.css # Styling for frontend
│ └── script.js # JavaScript logic (chart handling, frontend logic)
│
├── templates/ # HTML templates rendered via Flask
│ └── index.html
│
├── export_subnets.json # Exported subnet data (example output)
├── requirements.txt # Python dependencies
└── README.md # This file


---

## 🔧 Installation & Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ip-calculator.git
cd ip_calculator

2. Create and Activate Virtual Environment (Optional but Recommended)
bash
Copy
Edit
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

3. Install Required Python Packages
bash
Copy
Edit
pip install -r requirements.txt
4. Run the Flask App
bash
Copy
Edit
python app.py
5. Open in Browser
Visit: http://127.0.0.1:5000/
