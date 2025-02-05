import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import smtplib
from email.message import EmailMessage
import datetime
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Prasath@2002",
    database="vehicle_service_db"
)
cursor = conn.cursor()

# SMTP Email Function
def send_email(to_email, subject, body):
    sender_email = "prasath3428@gmail.com"
    sender_password = "tftn oxau nqlj etop"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Function to validate email
def is_valid_email(email):
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

# Function to validate phone number
def is_valid_phone(phone):
    regex = r'^\+?1?\d{9,15}$'
    return re.match(regex, phone)

# Function to register customer
def register_customer():
    name = name_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()

    if not is_valid_email(email):
        messagebox.showerror("Error", "Invalid email format!")
        return

    if not is_valid_phone(phone):
        messagebox.showerror("Error", "Invalid phone number format!")
        return

    if name and email and phone:
        cursor.execute("INSERT INTO customers (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
        conn.commit()
        messagebox.showinfo("Success", "Customer registered successfully!")
        load_customers()
    else:
        messagebox.showerror("Error", "All fields are required!")

# Function to update customer
def update_customer():
    selected_item = customer_tree.selection()[0]
    customer_id = customer_tree.item(selected_item, "values")[0]
    name = name_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()

    if not is_valid_email(email):
        messagebox.showerror("Error", "Invalid email format!")
        return

    if not is_valid_phone(phone):
        messagebox.showerror("Error", "Invalid phone number format!")
        return

    if name and email and phone:
        cursor.execute("UPDATE customers SET name = %s, email = %s, phone = %s WHERE id = %s", (name, email, phone, customer_id))
        conn.commit()
        messagebox.showinfo("Success", "Customer updated successfully!")
        load_customers()
    else:
        messagebox.showerror("Error", "All fields are required!")

# Function to delete customer
def delete_customer():
    selected_item = customer_tree.selection()[0]
    customer_id = customer_tree.item(selected_item, "values")[0]
    cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
    conn.commit()
    messagebox.showinfo("Success", "Customer deleted successfully!")
    load_customers()

# Function to search customers
def search_customers():
    search_term = search_entry.get()
    cursor.execute("SELECT * FROM customers WHERE name LIKE %s OR email LIKE %s", (f"%{search_term}%", f"%{search_term}%"))
    customers = cursor.fetchall()
    for row in customer_tree.get_children():
        customer_tree.delete(row)
    for customer in customers:
        customer_tree.insert("", "end", values=customer)

# Function to load customers
def load_customers():
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()
    for row in customer_tree.get_children():
        customer_tree.delete(row)
    for customer in customers:
        customer_tree.insert("", "end", values=customer)

# Function to fill customer data in entry fields
def fill_customer_data(event):
    selected_item = customer_tree.selection()[0]
    customer = customer_tree.item(selected_item, "values")
    name_entry.delete(0, tk.END)
    name_entry.insert(0, customer[1])
    email_entry.delete(0, tk.END)
    email_entry.insert(0, customer[2])
    phone_entry.delete(0, tk.END)
    phone_entry.insert(0, customer[3])

# Function to update vehicle models based on selected brand
def update_vehicle_models(event):
    brand = brand_combo.get()
    models = vehicle_data.get(brand, [])
    model_combo['values'] = models
    model_combo.set('')

# Function to auto-fill customer data
def autofill_customer_data(event):
    customer_id = cust_id_entry.get()
    cursor.execute("SELECT name, email, phone FROM customers WHERE id = %s", (customer_id,))
    customer = cursor.fetchone()
    if customer:
        name_entry.delete(0, tk.END)
        name_entry.insert(0, customer[0])
        email_entry.delete(0, tk.END)
        email_entry.insert(0, customer[1])
        phone_entry.delete(0, tk.END)
        phone_entry.insert(0, customer[2])
        # Get last service date
        cursor.execute("SELECT date FROM services WHERE customer_id = %s ORDER BY date DESC LIMIT 1", (customer_id,))
        last_service = cursor.fetchone()
        if last_service:
            last_service_date_entry.delete(0, tk.END)
            last_service_date_entry.insert(0, last_service[0])

# Function to book service
def book_service():
    customer_id = cust_id_entry.get()
    vehicle_brand = brand_combo.get()
    vehicle_model = model_combo.get()
    service_type = service_type_combo.get()
    date = date_entry.get()
    status = status_combo.get()

    if customer_id and vehicle_brand and vehicle_model and service_type and date and status:
        cursor.execute("INSERT INTO services (customer_id, vehicle_brand, vehicle_model, service_type, date, status) VALUES (%s, %s, %s, %s, %s, %s)",
                       (customer_id, vehicle_brand, vehicle_model, service_type, date, status))
        conn.commit()

        # Get customer email for confirmation
        cursor.execute("SELECT name, email FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        if customer:
            send_email(customer[1], "Service Booking Confirmation", f"Hello {customer[0]},\n\nYour vehicle ({vehicle_brand} {vehicle_model}) is scheduled for {service_type} on {date}.\n\nThank you!")

        messagebox.showinfo("Success", "Service booked successfully! Confirmation email sent.")
    else:
        messagebox.showerror("Error", "All fields are required!")

# Function to update service status
def update_service_status():
    selected_item = service_tree.selection()[0]
    service_id = service_tree.item(selected_item, "values")[0]
    status = status_combo.get()

    if status:
        cursor.execute("UPDATE services SET status = %s WHERE id = %s", (status, service_id))
        conn.commit()
        messagebox.showinfo("Success", "Service status updated successfully!")
        view_service_history()
        if status == "Completed":
            # Get customer email for notification
            cursor.execute("SELECT customers.email, customers.name, services.vehicle_brand, services.vehicle_model FROM services JOIN customers ON services.customer_id = customers.id WHERE services.id = %s", (service_id,))
            customer = cursor.fetchone()
            if customer:
                send_email(customer[0], "Service Completed", f"Hello {customer[1]},\n\nYour vehicle ({customer[2]} {customer[3]}) service has been completed.\n\nThank you!")
                generate_invoice(service_id)
    else:
        messagebox.showerror("Error", "Status is required!")

# Function to generate invoice
def generate_invoice(service_id):
    cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
    service = cursor.fetchone()
    if service:
        cursor.execute("SELECT name, email FROM customers WHERE id = %s", (service[1],))
        customer = cursor.fetchone()
        if customer:
            pdf = canvas.Canvas("invoice.pdf", pagesize=letter)
            pdf.setFont("Helvetica", 12)
            pdf.drawString(1 * inch, 10 * inch, "Invoice")
            pdf.drawString(1 * inch, 9.5 * inch, f"Customer Name: {customer[0]}")
            pdf.drawString(1 * inch, 9 * inch, f"Customer Email: {customer[1]}")
            pdf.drawString(1 * inch, 8.5 * inch, f"Vehicle Brand: {service[2]}")
            pdf.drawString(1 * inch, 8 * inch, f"Vehicle Model: {service[3]}")
            pdf.drawString(1 * inch, 7.5 * inch, f"Service Type: {service[4]}")
            pdf.drawString(1 * inch, 7 * inch, f"Service Date: {service[5]}")
            pdf.drawString(1 * inch, 6.5 * inch, f"Status: {service[6]}")
            pdf.save()
            messagebox.showinfo("Success", "Invoice generated successfully!")

# Function to view service history
def view_service_history():
    customer_id = cust_id_entry.get()
    cursor.execute("SELECT * FROM services WHERE customer_id = %s", (customer_id,))
    services = cursor.fetchall()
    for row in service_tree.get_children():
        service_tree.delete(row)
    for service in services:
        service_tree.insert("", "end", values=service)

# Vehicle data
vehicle_data = {
    "Toyota": ["Corolla", "Camry", "Prius"],
    "Honda": ["Civic", "Accord", "CR-V"],
    "Ford": ["Focus", "Fusion", "Mustang"],
    "Chevrolet": ["Malibu", "Impala", "Cruze"]
}

# Tkinter GUI Setup
root = tk.Tk()
root.title("Car Service Registration")

# Apply theme
style = ttk.Style()
style.configure("TLabel", font=("Helvetica", 12), padding=5)
style.configure("TButton", font=("Helvetica", 12), padding=5)
style.configure("TEntry", font=("Helvetica", 12), padding=5)
style.configure("TCombobox", font=("Helvetica", 12), padding=5)

# Customer Registration Frame
customer_frame = ttk.LabelFrame(root, text="Customer Registration", padding=(20, 10))
customer_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

ttk.Label(customer_frame, text="Customer Name").grid(row=0, column=0, padx=10, pady=10, sticky="ew")
name_entry = ttk.Entry(customer_frame, width=40)
name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

ttk.Label(customer_frame, text="Email").grid(row=1, column=0, padx=10, pady=10, sticky="ew")
email_entry = ttk.Entry(customer_frame, width=40)
email_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

ttk.Label(customer_frame, text="Phone").grid(row=2, column=0, padx=10, pady=10, sticky="ew")
phone_entry = ttk.Entry(customer_frame, width=40)
phone_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

ttk.Button(customer_frame, text="Register Customer", command=register_customer).grid(row=3, column=0, columnspan=2, pady=10)
ttk.Button(customer_frame, text="Update Customer", command=update_customer).grid(row=4, column=0, columnspan=2, pady=10)
ttk.Button(customer_frame, text="Delete Customer", command=delete_customer).grid(row=5, column=0, columnspan=2, pady=10)

# Service Booking Frame
service_frame = ttk.LabelFrame(root, text="Service Booking", padding=(20, 10))
service_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

ttk.Label(service_frame, text="Customer ID").grid(row=0, column=0, padx=10, pady=10, sticky="ew")
cust_id_entry = ttk.Entry(service_frame, width=40)
cust_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
cust_id_entry.bind("<FocusOut>", autofill_customer_data)

ttk.Label(service_frame, text="Vehicle Brand").grid(row=1, column=0, padx=10, pady=10, sticky="ew")
brand_combo = ttk.Combobox(service_frame, values=list(vehicle_data.keys()), width=38)
brand_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
brand_combo.bind("<<ComboboxSelected>>", update_vehicle_models)

ttk.Label(service_frame, text="Vehicle Model").grid(row=2, column=0, padx=10, pady=10, sticky="ew")
model_combo = ttk.Combobox(service_frame, width=38)
model_combo.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

ttk.Label(service_frame, text="Service Type").grid(row=3, column=0, padx=10, pady=10, sticky="ew")
service_type_combo = ttk.Combobox(service_frame, values=["Oil Change", "General Service", "Brake Check", "Tire Replacement"], width=38)
service_type_combo.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

ttk.Label(service_frame, text="Service Date (YYYY-MM-DD)").grid(row=4, column=0, padx=10, pady=10, sticky="ew")
date_entry = ttk.Entry(service_frame, width=40)
date_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

ttk.Label(service_frame, text="Status").grid(row=5, column=0, padx=10, pady=10, sticky="ew")
status_combo = ttk.Combobox(service_frame, values=["Pending", "In Progress", "Completed"], width=38)
status_combo.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

ttk.Button(service_frame, text="Book Service", command=book_service).grid(row=6, column=0, columnspan=2, pady=10)
ttk.Button(service_frame, text="Generate Invoice", command=generate_invoice).grid(row=7, column=0, columnspan=2, pady=10)

# Customer List Frame
customer_list_frame = ttk.LabelFrame(root, text="Customer List", padding=(20, 10))
customer_list_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

ttk.Label(customer_list_frame, text="Search").grid(row=0, column=0, padx=10, pady=10, sticky="ew")
search_entry = ttk.Entry(customer_list_frame, width=40)
search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
ttk.Button(customer_list_frame, text="Search", command=search_customers).grid(row=0, column=2, padx=10, pady=10, sticky="ew")

customer_tree = ttk.Treeview(customer_list_frame, columns=("ID", "Name", "Email", "Phone"), show="headings")
customer_tree.heading("ID", text="ID")
customer_tree.heading("Name", text="Name")
customer_tree.heading("Email", text="Email")
customer_tree.heading("Phone", text="Phone")
customer_tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
customer_tree.bind("<ButtonRelease-1>", fill_customer_data)

# Service History Frame
service_history_frame = ttk.LabelFrame(root, text="Service History", padding=(20, 10))
service_history_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

ttk.Button(service_history_frame, text="View Service History", command=view_service_history).grid(row=0, column=0, columnspan=2, pady=10)

service_tree = ttk.Treeview(service_history_frame, columns=("ID", "Customer ID", "Vehicle Brand", "Vehicle Model", "Service Type", "Date", "Status"), show="headings")
service_tree.heading("ID", text="ID")
service_tree.heading("Customer ID", text="Customer ID")
service_tree.heading("Vehicle Brand", text="Vehicle Brand")
service_tree.heading("Vehicle Model", text="Vehicle Model")
service_tree.heading("Service Type", text="Service Type")
service_tree.heading("Date", text="Date")
service_tree.heading("Status", text="Status")
service_tree.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
service_tree.bind("<ButtonRelease-1>", lambda event: status_combo.set(service_tree.item(service_tree.selection()[0], "values")[6]))

# Last Service Date Entry
ttk.Label(service_frame, text="Last Service Date").grid(row=8, column=0, padx=10, pady=10, sticky="ew")
last_service_date_entry = ttk.Entry(service_frame, width=40)
last_service_date_entry.grid(row=8, column=1, padx=10, pady=10, sticky="ew")

# Update Service Status Button
ttk.Button(service_frame, text="Update Service Status", command=update_service_status).grid(row=9, column=0, columnspan=2, pady=10)

load_customers()

root.mainloop()