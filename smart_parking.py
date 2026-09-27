import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import math
import re

DB_NAME = "smart_parking.db"
TOTAL_SLOTS = 50
RATE_PER_HOUR = 100

class ParkingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Parking Management System")
        self.root.geometry("1050x680")
        self.root.minsize(900, 600)

        self.create_database()
        self.build_interface()
        self.refresh_all()

        # The application keeps running continuously through Tkinter's mainloop.
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def connect(self):
        return sqlite3.connect(DB_NAME)

    def create_database(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(""" CREATE TABLE IF NOT EXISTS parking_lot ( id INTEGER PRIMARY KEY, total_slots INTEGER NOT NULL, available_slots INTEGER NOT NULL ) """)

        cur.execute(""" CREATE TABLE IF NOT EXISTS parking_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, registration TEXT NOT NULL, vehicle_type TEXT NOT NULL, entry_time TEXT NOT NULL, exit_time TEXT, duration_hours REAL, amount REAL, payment_method TEXT, payment_status TEXT DEFAULT 'PENDING', mpesa_phone TEXT, status TEXT NOT NULL ) """)

        cur.execute("SELECT COUNT(*) FROM parking_lot")
        if cur.fetchone()[0] == 0:
            cur.execute(""" INSERT INTO parking_lot (id, total_slots, available_slots) VALUES (1, ?, ?) """, (TOTAL_SLOTS, TOTAL_SLOTS))

        conn.commit()
        conn.close()

    def build_interface(self):
        self.root.configure(bg="#eef2f7")

        title = tk.Label(
            self.root,
            text="SMART PARKING MANAGEMENT SYSTEM",
            font=("Arial", 22, "bold"),
            bg="#17365d",
            fg="white",
            pady=18
        )
        title.pack(fill="x")

        top = tk.Frame(self.root, bg="#eef2f7")
        top.pack(fill="x", padx=20, pady=15)

        self.total_label = tk.Label(
            top, text="Total: 0", font=("Arial", 15, "bold"),
            bg="#eef2f7"
        )
        self.total_label.pack(side="left", padx=15)

        self.available_label = tk.Label(
            top, text="Available: 0", font=("Arial", 15, "bold"),
            bg="#eef2f7"
        )
        self.available_label.pack(side="left", padx=15)

        self.occupied_label = tk.Label(
            top, text="Occupied: 0", font=("Arial", 15, "bold"),
            bg="#eef2f7"
        )
        self.occupied_label.pack(side="left", padx=15)

        self.status_label = tk.Label(
            top, text="STATUS", font=("Arial", 15, "bold"),
            bg="#eef2f7"
        )
        self.status_label.pack(side="right", padx=15)

        form = tk.LabelFrame(
            self.root,
            text="Vehicle Entry",
            font=("Arial", 12, "bold"),
            bg="#eef2f7",
            padx=15,
            pady=12
        )
        form.pack(fill="x", padx=20, pady=5)

        tk.Label(form, text="Registration:", bg="#eef2f7").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.registration_entry = tk.Entry(form, width=25, font=("Arial", 12))
        self.registration_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Vehicle Type:", bg="#eef2f7").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.vehicle_type = ttk.Combobox(
            form,
            values=["Car", "Motorcycle", "Van", "Truck", "Bus"],
            state="readonly",
            width=20
        )
        self.vehicle_type.current(0)
        self.vehicle_type.grid(row=0, column=3, padx=5, pady=5)

        enter_button = tk.Button(
            form,
            text="VEHICLE ENTRY",
            command=self.vehicle_entry,
            font=("Arial", 11, "bold"),
            bg="#2e7d32",
            fg="white",
            padx=15,
            pady=8
        )
        enter_button.grid(row=0, column=4, padx=15)

        exit_frame = tk.LabelFrame(
            self.root,
            text="Vehicle Exit & M-Pesa Payment",
            font=("Arial", 12, "bold"),
            bg="#eef2f7",
            padx=15,
            pady=12
        )
        exit_frame.pack(fill="x", padx=20, pady=8)

        tk.Label(exit_frame, text="Registration:", bg="#eef2f7").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.exit_registration = tk.Entry(
            exit_frame, width=20, font=("Arial", 12)
        )
        self.exit_registration.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(exit_frame, text="M-Pesa Phone:", bg="#eef2f7").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.phone_entry = tk.Entry(
            exit_frame, width=20, font=("Arial", 12)
        )
        self.phone_entry.insert(0, "07")
        self.phone_entry.grid(row=0, column=3, padx=5, pady=5)

        exit_button = tk.Button(
            exit_frame,
            text="PROCESS EXIT + M-PESA",
            command=self.vehicle_exit,
            font=("Arial", 11, "bold"),
            bg="#00897b",
            fg="white",
            padx=15,
            pady=8
        )
        exit_button.grid(row=0, column=4, padx=15)

        button_frame = tk.Frame(self.root, bg="#eef2f7")
        button_frame.pack(fill="x", padx=20, pady=8)

        tk.Button(
            button_frame, text="Refresh",
            command=self.refresh_all,
            width=15, font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame, text="Parking History",
            command=self.show_history,
            width=15, font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame, text="Clear Entry Fields",
            command=self.clear_fields,
            width=18, font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        table_frame = tk.LabelFrame(
            self.root,
            text="Vehicles Currently Inside",
            font=("Arial", 12, "bold"),
            bg="#eef2f7",
            padx=10,
            pady=10
        )
        table_frame.pack(fill="both", expand=True, padx=20, pady=5)

        columns = ("registration", "type", "entry_time")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )

        self.tree.heading("registration", text="Registration")
        self.tree.heading("type", text="Vehicle Type")
        self.tree.heading("entry_time", text="Entry Time")

        self.tree.column("registration", width=180, anchor="center")
        self.tree.column("type", width=180, anchor="center")
        self.tree.column("entry_time", width=250, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def get_availability(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(""" SELECT total_slots, available_slots FROM parking_lot WHERE id = 1 """)
        result = cur.fetchone()
        conn.close()
        return result

    def refresh_all(self):
        total, available = self.get_availability()
        occupied = total - available

        self.total_label.config(text=f"Total: {total}")
        self.available_label.config(text=f"Available: {available}")
        self.occupied_label.config(text=f"Occupied: {occupied}")

        if available == 0:
            self.status_label.config(text="PARKING FULL", fg="red")
        else:
            self.status_label.config(text="SPACES AVAILABLE", fg="green")

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.connect()
        cur = conn.cursor()
        cur.execute(""" SELECT registration, vehicle_type, entry_time FROM parking_records WHERE status = 'PARKED' ORDER BY entry_time """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", "end", values=row)

    def vehicle_entry(self):
        registration = self.registration_entry.get().strip().upper()
        vehicle_type = self.vehicle_type.get()

        if not registration:
            messagebox.showwarning(
                "Missing Information",
                "Enter the vehicle registration number."
            )
            return

        total, available = self.get_availability()

        if available <= 0:
            messagebox.showerror(
                "Parking Full",
                "The parking lot is full. No vehicle can enter."
            )
            return

        conn = self.connect()
        cur = conn.cursor()

        cur.execute(""" SELECT id FROM parking_records WHERE registration = ? AND status = 'PARKED' """, (registration,))

        if cur.fetchone():
            conn.close()
            messagebox.showwarning(
                "Already Inside",
                f"{registration} is already inside the parking lot."
            )
            return

        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(""" INSERT INTO parking_records (registration, vehicle_type, entry_time, status) VALUES (?, ?, ?, 'PARKED') """, (registration, vehicle_type, entry_time))

        cur.execute(""" UPDATE parking_lot SET available_slots = available_slots - 1 WHERE id = 1 """)

        conn.commit()
        conn.close()

        self.clear_entry_only()
        self.refresh_all()

        messagebox.showinfo(
            "Vehicle Entry Recorded",
            f"Vehicle: {registration}\n"
            f"Type: {vehicle_type}\n"
            f"Entry time: {entry_time}\n\n"
            f"One parking slot has been occupied."
        )

    def valid_phone(self, phone):
        phone = phone.strip().replace(" ", "")
        return bool(re.fullmatch(r"(07|01)\d{8}", phone))

    def vehicle_exit(self):
        registration = self.exit_registration.get().strip().upper()
        phone = self.phone_entry.get().strip().replace(" ", "")

        if not registration:
            messagebox.showwarning(
                "Missing Information",
                "Enter the vehicle registration number."
            )
            return

        if not self.valid_phone(phone):
            messagebox.showwarning(
                "Invalid M-Pesa Number",
                "Enter a valid Kenyan number, for example 0712345678."
            )
            return

        conn = self.connect()
        cur = conn.cursor()

        cur.execute(""" SELECT id, vehicle_type, entry_time FROM parking_records WHERE registration = ? AND status = 'PARKED' """, (registration,))

        vehicle = cur.fetchone()

        if not vehicle:
            conn.close()
            messagebox.showerror(
                "Vehicle Not Found",
                "That vehicle is not currently recorded as being inside."
            )
            return

        record_id, vehicle_type, entry_text = vehicle

        entry_time = datetime.strptime(
            entry_text, "%Y-%m-%d %H:%M:%S"
        )
        exit_time = datetime.now()

        seconds = (exit_time - entry_time).total_seconds()
        duration_hours = seconds / 3600
        billed_hours = max(1, math.ceil(duration_hours))
        amount = billed_hours * RATE_PER_HOUR

        exit_text = exit_time.strftime("%Y-%m-%d %H:%M:%S")

        # This is a local/demo M-Pesa payment workflow.
        # Real Safaricom STK Push requires Daraja API credentials.
        payment_ok = self.mpesa_payment_demo(
            registration, phone, amount
        )

        if not payment_ok:
            conn.close()
            return

        cur.execute(""" UPDATE parking_records SET exit_time = ?, duration_hours = ?, amount = ?, payment_method = 'M-PESA', payment_status = 'PAID', mpesa_phone = ?, status = 'EXITED' WHERE id = ? """, (
            exit_text,
            duration_hours,
            amount,
            phone,
            record_id
        ))

        cur.execute(""" UPDATE parking_lot SET available_slots = available_slots + 1 WHERE id = 1 """)

        conn.commit()
        conn.close()

        self.refresh_all()
        self.exit_registration.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, "07")

        messagebox.showinfo(
            "Payment Successful",
            f"M-PESA PAYMENT\n\n"
            f"Vehicle: {registration}\n"
            f"Phone: {phone}\n"
            f"Entry: {entry_text}\n"
            f"Exit: {exit_text}\n"
            f"Time spent: {duration_hours:.2f} hours\n"
            f"Billed hours: {billed_hours}\n"
            f"Amount paid: KSh {amount:.2f}\n\n"
            f"Payment method: M-PESA\n"
            f"Payment status: PAID\n\n"
            f"Parking slot has been returned."
        )

    def mpesa_payment_demo(self, registration, phone, amount):
        answer = messagebox.askyesno(
            "M-Pesa Payment",
            f"Send M-Pesa payment request?\n\n"
            f"Vehicle: {registration}\n"
            f"Phone: {phone}\n"
            f"Amount: KSh {amount:.2f}\n\n"
            f"Click YES to simulate a successful M-Pesa payment."
        )

        return answer

    def show_history(self):
        window = tk.Toplevel(self.root)
        window.title("Parking History")
        window.geometry("1050x500")

        columns = (
            "registration", "type", "entry", "exit",
            "duration", "amount", "payment"
        )

        tree = ttk.Treeview(
            window, columns=columns, show="headings"
        )

        headings = {
            "registration": "Registration",
            "type": "Vehicle Type",
            "entry": "Entry",
            "exit": "Exit",
            "duration": "Hours",
            "amount": "Amount",
            "payment": "Payment"
        }

        widths = {
            "registration": 130,
            "type": 120,
            "entry": 170,
            "exit": 170,
            "duration": 80,
            "amount": 100,
            "payment": 100
        }

        for column in columns:
            tree.heading(column, text=headings[column])
            tree.column(column, width=widths[column], anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        conn = self.connect()
        cur = conn.cursor()
        cur.execute(""" SELECT registration, vehicle_type, entry_time, exit_time, duration_hours, amount, payment_method FROM parking_records WHERE status = 'EXITED' ORDER BY exit_time DESC """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            values = list(row)
            if values[4] is not None:
                values[4] = f"{values[4]:.2f}"
            if values[5] is not None:
                values[5] = f"KSh {values[5]:.2f}"
            tree.insert("", "end", values=values)

    def clear_entry_only(self):
        self.registration_entry.delete(0, tk.END)
        self.vehicle_type.current(0)

    def clear_fields(self):
        self.clear_entry_only()
        self.exit_registration.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, "07")

    def close_application(self):
        if messagebox.askyesno(
            "Exit System",
            "Are you sure you want to close the parking system?"
        ):
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingSystem(root)
    root.mainloop()