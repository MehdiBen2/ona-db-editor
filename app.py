import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import pandas as pd

class EditableTable(ttk.Treeview):
    def __init__(self, master, columns, on_cell_edit=None, on_delete=None):
        super().__init__(master, columns=columns, show='headings')
        
        self.on_cell_edit = on_cell_edit
        self.on_delete = on_delete
        
        # Configure columns
        for col in columns:
            self.heading(col, text=col)
            self.column(col, width=100)  # Default width
        
        # Bind double-click event
        self.bind('<Double-1>', self.on_double_click)
        
        # Create scrollbars
        self.vsb = ttk.Scrollbar(master, orient="vertical", command=self.yview)
        self.hsb = ttk.Scrollbar(master, orient="horizontal", command=self.xview)
        self.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        # Grid layout
        self.grid(row=0, column=0, sticky='nsew')
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.hsb.grid(row=1, column=0, sticky='ew')

    def on_double_click(self, event):
        region = self.identify("region", event.x, event.y)
        if region == "cell":
            # Get the clicked item and column
            item = self.identify_row(event.y)
            column = self.identify_column(event.x)
            column_index = int(column[1]) - 1  # Convert #1, #2 etc to 0, 1 etc
            
            if item and column:
                self.create_edit_widget(item, column, column_index)

    def create_edit_widget(self, item, column, column_index):
        # Get current value and bounds
        current_value = self.item(item, "values")[column_index]
        x, y, w, h = self.bbox(item, column)
        
        # Create editing frame
        frame = ttk.Frame(self)
        frame.place(x=x, y=y, width=w, height=h)
        
        # Create entry widget
        entry = ttk.Entry(frame)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.pack(fill=tk.BOTH, expand=True)
        entry.focus_set()
        
        def save_edit(event=None):
            new_value = entry.get()
            values = list(self.item(item, "values"))
            values[column_index] = new_value
            self.item(item, values=values)
            
            if self.on_cell_edit:
                self.on_cell_edit(item, column_index, new_value)
            frame.destroy()
            
        def cancel_edit(event=None):
            frame.destroy()
            
        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', save_edit)

    def load_data(self, data):
        """Load data into the table"""
        # Clear existing items
        for item in self.get_children():
            self.delete(item)
            
        # Insert new data
        for row in data:
            # Convert all values to strings to avoid display issues
            str_row = [str(val) if val is not None else '' for val in row]
            self.insert("", "end", values=str_row)

    def add_row(self, values):
        """Add a new row to the table"""
        # Convert values to strings
        str_values = [str(val) if val is not None else '' for val in values]
        self.insert("", "end", values=str_values)

class DatabaseManager(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Database Manager")
        self.geometry("1000x600")
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Variables
        self.current_db = None
        self.current_table = None
        self.edited_data = {}

        # Create GUI elements
        self.create_top_frame()
        self.create_main_frame()

    def create_top_frame(self):
        # Top frame for controls
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Buttons
        self.open_btn = ttk.Button(
            self.top_frame,
            text="Open Database",
            command=self.open_database
        )
        self.open_btn.pack(side="left", padx=5)
        
        # Tables dropdown
        self.tables_var = tk.StringVar(value="No database opened")
        self.tables_dropdown = ttk.Combobox(
            self.top_frame,
            textvariable=self.tables_var,
            state="readonly"
        )
        self.tables_dropdown.pack(side="left", padx=5)
        self.tables_dropdown.bind('<<ComboboxSelected>>', 
            lambda e: self.load_table_data(self.tables_var.get()))
        
        # Save button
        self.save_btn = ttk.Button(
            self.top_frame,
            text="Save Changes",
            command=self.save_changes,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Add row button
        self.add_row_btn = ttk.Button(
            self.top_frame,
            text="Add Row",
            command=self.add_new_row,
            state="disabled"
        )
        self.add_row_btn.pack(side="left", padx=5)
        
        # Add delete button
        self.delete_btn = ttk.Button(
            self.top_frame,
            text="Delete Row",
            command=self.delete_selected_row,
            state="disabled"
        )
        self.delete_btn.pack(side="left", padx=5)

    def create_main_frame(self):
        # Main frame for data display
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def open_database(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.current_db = sqlite3.connect(file_path)
                self.load_tables()
                messagebox.showinfo("Success", "Database opened successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to open database: {str(e)}")

    def load_tables(self):
        cursor = self.current_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if table_names:
            self.tables_dropdown['values'] = table_names
            self.tables_var.set(table_names[0])
            self.load_table_data(table_names[0])
        else:
            messagebox.showinfo("Info", "No tables found in database")

    def on_cell_edit(self, item, col, new_value):
        if not self.current_table:
            return
            
        try:
            # Get all values for this row
            values = self.table.item(item)['values']
            row_id = values[0] if values else None  # First column as ID
            column_name = self.table['columns'][col]
            
            # Store the edit
            if row_id:
                if row_id not in self.edited_data:
                    self.edited_data[row_id] = {}
                self.edited_data[row_id][column_name] = new_value
            
            # Enable save button
            self.save_btn['state'] = 'normal'
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to track edit: {str(e)}")

    def load_table_data(self, table_name):
        if not self.current_db or not table_name:
            return
            
        self.current_table = table_name
        self.edited_data = {}
        
        try:
            # Get table structure
            cursor = self.current_db.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Get data
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.current_db)
            
            # Clear main frame
            for widget in self.main_frame.winfo_children():
                widget.destroy()
                
            # Create table with column info and delete callback
            self.table = EditableTable(
                self.main_frame,
                columns=list(df.columns),
                on_cell_edit=self.on_cell_edit,
                on_delete=self.delete_selected_row
            )
            
            # Bind selection event
            self.table.bind('<<TreeviewSelect>>', self.on_row_select)
            
            # Store column info for validation
            self.table.columns_info = {
                col[1]: {'type': col[2], 'notnull': col[3], 'pk': col[5]}
                for col in columns_info
            }
            
            # Load data
            self.table.load_data(df.values.tolist())
            
            # Enable buttons
            self.save_btn['state'] = 'normal'
            self.add_row_btn['state'] = 'normal'
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table: {str(e)}")

    def on_row_select(self, event):
        """Enable/disable delete button based on selection"""
        selected = self.table.selection()
        self.delete_btn['state'] = 'normal' if selected else 'disabled'

    def delete_selected_row(self):
        """Delete selected row(s) from table and database"""
        selected = self.table.selection()
        if not selected:
            return
            
        if not messagebox.askyesno("Confirm Delete", 
                                  "Are you sure you want to delete the selected row(s)?"):
            return
            
        try:
            cursor = self.current_db.cursor()
            
            for item in selected:
                # Get row values
                values = self.table.item(item)['values']
                row_id = values[0] if values else None
                
                if row_id:
                    # Delete from database
                    query = f"""
                    DELETE FROM {self.current_table}
                    WHERE {self.table['columns'][0]} = ?
                    """
                    
                    try:
                        cursor.execute(query, [row_id])
                    except sqlite3.Error as e:
                        messagebox.showerror("Error", f"Failed to delete row {row_id}: {str(e)}")
                        continue
                
                # Delete from table display
                self.table.delete(item)
            
            self.current_db.commit()
            messagebox.showinfo("Success", "Selected row(s) deleted successfully!")
            
            # Disable delete button after deletion
            self.delete_btn['state'] = 'disabled'
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete row(s): {str(e)}")
            self.current_db.rollback()

    def add_new_row(self):
        if not self.current_table or not hasattr(self, 'table'):
            return
            
        try:
            # Create dialog to get row details
            dialog = tk.Toplevel(self)
            dialog.title("Add New Row")
            dialog.geometry("400x300")
            
            # Get column names and types from current table
            cursor = self.current_db.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            
            # Create entry fields for each column
            entries = {}
            for i, col_info in enumerate(columns_info):
                name, type_ = col_info[1], col_info[2]
                
                frame = ttk.Frame(dialog)
                frame.pack(fill='x', padx=10, pady=5)
                
                ttk.Label(frame, text=f"{name} ({type_}):").pack(side='left')
                entry = ttk.Entry(frame)
                entry.pack(side='right', expand=True, fill='x', padx=5)
                entries[name] = entry

            def submit():
                try:
                    # Get values from entries
                    values = []
                    for col_info in columns_info:
                        name = col_info[1]
                        value = entries[name].get()
                        
                        # Convert empty strings to NULL for SQLite
                        if value == '':
                            value = None
                        values.append(value)
                    
                    # Insert into database
                    placeholders = ','.join(['?' for _ in values])
                    columns = ','.join([col[1] for col in columns_info])
                    
                    cursor = self.current_db.cursor()
                    cursor.execute(f"""
                        INSERT INTO {self.current_table} ({columns})
                        VALUES ({placeholders})
                    """, values)
                    
                    self.current_db.commit()
                    
                    # Add to table display
                    self.table.add_row(values)
                    
                    dialog.destroy()
                    messagebox.showinfo("Success", "Row added successfully!")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add row: {str(e)}")

            # Add submit button
            ttk.Button(dialog, text="Add Row", command=submit).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add new row: {str(e)}")

    def save_changes(self):
        if not self.current_db or not self.current_table:
            messagebox.showinfo("Info", "No database or table selected!")
            return
            
        try:
            cursor = self.current_db.cursor()
            
            # Get all rows from the table
            for item in self.table.get_children():
                values = self.table.item(item)['values']
                row_id = values[0] if values else None
                
                if row_id:  # Existing row
                    if row_id in self.edited_data:
                        # Update existing row
                        changes = self.edited_data[row_id]
                        set_clause = ", ".join([f"{col} = ?" for col in changes.keys()])
                        values = list(changes.values())
                        
                        query = f"""
                        UPDATE {self.current_table}
                        SET {set_clause}
                        WHERE {self.table['columns'][0]} = ?
                        """
                        
                        try:
                            cursor.execute(query, values + [row_id])
                        except sqlite3.Error as e:
                            messagebox.showerror("Error", f"Failed to update row {row_id}: {str(e)}")
                            continue
                else:  # New row
                    # Insert new row
                    columns = self.table['columns']
                    values = self.table.item(item)['values']
                    
                    # Skip empty rows
                    if not any(values):
                        continue
                        
                    placeholders = ", ".join(["?" for _ in columns])
                    columns_str = ", ".join(columns)
                    
                    query = f"""
                    INSERT INTO {self.current_table} ({columns_str})
                    VALUES ({placeholders})
                    """
                    
                    try:
                        cursor.execute(query, values)
                    except sqlite3.Error as e:
                        messagebox.showerror("Error", f"Failed to insert new row: {str(e)}")
                        continue
            
            self.current_db.commit()
            self.edited_data = {}
            messagebox.showinfo("Success", "Changes saved successfully!")
            
            # Reload table data
            self.load_table_data(self.current_table)
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
            self.current_db.rollback()

if __name__ == "__main__":
    app = DatabaseManager()
    app.mainloop()
