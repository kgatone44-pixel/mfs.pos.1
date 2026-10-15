from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'mfs_pos_super_secret_key'

# Database Setup & Initialization with Migration check
def init_db():
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            shop_name TEXT NOT NULL
        )
    ''')
    
    # Transactions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tx_type TEXT NOT NULL,
            account TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL,
            note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Shop Accounts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_name TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER;")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE shop_accounts ADD COLUMN user_id INTEGER;")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('mfs_pos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['user'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        shop_name = request.form.get('shop_name')
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('mfs_pos.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (username, password, shop_name) VALUES (?, ?, ?)", (username, password, shop_name))
            conn.commit()
            
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            new_user_id = cursor.fetchone()[0]
            
            default_accounts = [('KBZ Pay Agent', 1500000), ('Wave Money', 800000), ('AYA Pay', 450000), ('CB Pay', 300000)]
            for acc, bal in default_accounts:
                cursor.execute("INSERT INTO shop_accounts (user_id, account_name, balance) VALUES (?, ?, ?)", (new_user_id, acc, bal))
            conn.commit()
            conn.close()
            
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="ဤ Username မှာ အသုံးပြုပြီးသား ဖြစ်နေပါသည်။")
            
    return render_template('register.html')

@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT shop_name, username FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    shop_name = user_data[0] if user_data else "POS User"
    username = user_data[1] if user_data else "user"
    
    cursor.execute("SELECT tx_type, account, phone_number, amount, fee, note, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
    recent_transactions = cursor.fetchall()
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND tx_type = 'cash_in'", (user_id,))
    res_in = cursor.fetchone()[0]
    total_cash_in = res_in if res_in is not None else 0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND tx_type = 'cash_out'", (user_id,))
    res_out = cursor.fetchone()[0]
    total_cash_out = res_out if res_out is not None else 0
    
    cursor.execute("SELECT SUM(fee) FROM transactions WHERE user_id = ?", (user_id,))
    res_fee = cursor.fetchone()[0]
    total_commission = res_fee if res_fee is not None else 0
    
    cursor.execute("SELECT account_name, balance FROM shop_accounts WHERE user_id = ?", (user_id,))
    accounts = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        'dashboard.html', 
        transactions=recent_transactions,
        total_cash_in=total_cash_in,
        total_cash_out=total_cash_out,
        total_commission=total_commission,
        accounts=accounts,
        shop_name=shop_name,
        username=username
    )

@app.route('/account_settings', methods=['GET', 'POST'])
def account_settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    
    error = None
    success = None
    
    if request.method == 'POST':
        new_shop_name = request.form.get('shop_name')
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        
        try:
            if new_password:
                cursor.execute("UPDATE users SET shop_name = ?, username = ?, password = ? WHERE id = ?", 
                               (new_shop_name, new_username, new_password, user_id))
            else:
                cursor.execute("UPDATE users SET shop_name = ?, username = ? WHERE id = ?", 
                               (new_shop_name, new_username, user_id))
            conn.commit()
            session['user'] = new_username
            success = "အကောင့်အချက်အလက်များကို အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။"
        except sqlite3.IntegrityError:
            error = "ဤ Username မှာ အသုံးပြုပြီးသား ဖြစ်နေပါသည်။"
            
    cursor.execute("SELECT username, shop_name FROM users WHERE id = ?", (user_id,))
    current_user = cursor.fetchone()
    conn.close()
    
    return render_template('account_settings.html', user=current_user, error=error, success=success)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    tx_type = request.form.get('tx_type')
    account = request.form.get('account')
    phone_number = request.form.get('phone_number')
    amount = float(request.form.get('amount', 0))
    fee = float(request.form.get('fee', 0))
    note = request.form.get('note', '')

    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions (user_id, tx_type, account, phone_number, amount, fee, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, tx_type, account, phone_number, amount, fee, note))
    
    if tx_type == 'cash_in':
        cursor.execute("UPDATE shop_accounts SET balance = balance + ? WHERE user_id = ? AND account_name = ?", (amount, user_id, account))
    else:
        cursor.execute("UPDATE shop_accounts SET balance = balance - ? WHERE user_id = ? AND account_name = ?", (amount, user_id, account))
        
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT tx_type, account, phone_number, amount, fee, note, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC", (user_id,))
    all_transactions = cursor.fetchall()
    conn.close()
    return render_template('history.html', transactions=all_transactions)

@app.route('/accounts')
@app.route('/manage_accounts', methods=['GET', 'POST'])
def manage_accounts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            acc_name = request.form.get('account_name')
            initial_bal = float(request.form.get('initial_balance', 0))
            if acc_name:
                cursor.execute("INSERT INTO shop_accounts (user_id, account_name, balance) VALUES (?, ?, ?)", (user_id, acc_name, initial_bal))
                conn.commit()
                
        elif action == 'edit_all':
            total_count = int(request.form.get('total_count', 0))
            for i in range(total_count):
                acc_id = request.form.get(f'account_id_{i}')
                new_name = request.form.get(f'account_name_{i}')
                new_bal = float(request.form.get(f'balance_{i}', 0))
                if acc_id:
                    cursor.execute("UPDATE shop_accounts SET account_name = ?, balance = ? WHERE id = ? AND user_id = ?", (new_name, new_bal, acc_id, user_id))
            conn.commit()
            
    cursor.execute("SELECT id, account_name, balance FROM shop_accounts WHERE user_id = ?", (user_id,))
    accounts_list = cursor.fetchall()
    conn.close()
    return render_template('manage_accounts.html', accounts=accounts_list)

@app.route('/delete_account/<int:acc_id>', methods=['POST'])
def delete_account(acc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shop_accounts WHERE id = ? AND user_id = ?", (acc_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_accounts'))

@app.route('/shift_close')
def shift_close():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = sqlite3.connect('mfs_pos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND tx_type = 'cash_in'", (user_id,))
    total_in = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND tx_type = 'cash_out'", (user_id,))
    total_out = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(fee) FROM transactions WHERE user_id = ?", (user_id,))
    total_fee = cursor.fetchone()[0] or 0
    conn.close()
    return render_template('shift_close.html', total_in=total_in, total_out=total_out, total_fee=total_fee)

@app.route('/printer_setup')
def printer_setup():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('printer_setup.html')

@app.route('/backup')
def backup():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db_path = 'mfs_pos.db'
    if os.path.exists(db_path):
        return send_file(db_path, as_attachment=True)
    return "Database ဖိုင် မရှိသေးပါ။", 404

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)