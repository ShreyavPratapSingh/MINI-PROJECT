from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector, subprocess, random, re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'smart_vote_secret_key_2026'

# DB CONNECT
db = mysql.connector.connect(host="localhost", user="root", password="", database="smartvoting")
cursor = db.cursor()

def encrypt_vote(data):
    try:
        return subprocess.run(['./encrypt.exe', str(data)], capture_output=True, text=True, timeout=3).stdout.strip()
    except:
        return str(data)

# 1. FIRST PAGE - VOTER LOGIN
@app.route('/')
def index():
    return render_template('voter_login.html')

# 2. REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        aadhar = request.form['aadhar']
        mobile = request.form['mobile']
        password = request.form['password']

        if not re.match(r'^\d{12}$', aadhar):
            flash("Invalid Aadhar - 12 digits only")
            return redirect('/register')

        cursor.execute("SELECT * FROM voters WHERE aadhar=%s", (aadhar,))
        if cursor.fetchone():
            flash("Aadhar already registered")
            return redirect('/register')

        otp = str(random.randint(100000, 999999)) # FIXED: 6 digit OTP
        cursor.execute("CREATE TABLE IF NOT EXISTS aadhar_otp(aadhar VARCHAR(12) PRIMARY KEY, otp VARCHAR(6))")
        cursor.execute("REPLACE INTO aadhar_otp(aadhar, otp) VALUES(%s,%s)", (aadhar, otp))
        db.commit()
        print(f"\n=========== OTP FOR {mobile}: {otp} ===========\n")

        return render_template('verify_otp.html', name=name, aadhar=aadhar, mobile=mobile, password=password)

    return render_template('register.html')

# 3. VERIFY OTP
@app.route('/verify', methods=['POST'])
def verify():
    name = request.form['name']
    aadhar = request.form['aadhar']
    mobile = request.form['mobile']
    password = request.form['password']
    otp = request.form['otp']

    cursor.execute("SELECT otp FROM aadhar_otp WHERE aadhar=%s", (aadhar,))
    real_otp = cursor.fetchone()

    if real_otp and real_otp[0] == otp:
        pwd_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO voters(name, aadhar, mobile, password, has_voted) VALUES(%s,%s,%s,%s,0)",
                      (name, aadhar, mobile, pwd_hash))
        db.commit()
        flash("Registration Successful! Login Now")
        return redirect('/')
    else:
        flash("Wrong OTP")
        return redirect('/register')

# 4. VOTER LOGIN
@app.route('/login', methods=['POST'])
def login():
    aadhar = request.form['aadhar']
    password = request.form['password']
    cursor.execute("SELECT * FROM voters WHERE aadhar=%s", (aadhar,))
    user = cursor.fetchone()

    if user and check_password_hash(user[4], password):
        if user[5] == 1:
            flash("You have already voted")
            return redirect('/')
        session['voter_id'] = user[0]
        return redirect('/vote')
    else:
        flash("Invalid Credentials")
        return redirect('/')

# 5. VOTE PAGE
@app.route('/vote')
def vote():
    if 'voter_id' not in session:
        return redirect('/')
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    return render_template('vote.html', candidates=candidates)

# 6. SUBMIT VOTE - YEHI FIX HAI
@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    try:
        candidate_id = request.form['candidate']
        voter_id = session['voter_id']
        encrypted = encrypt_vote(candidate_id)

        # 1. Vote save karo
        cursor.execute("INSERT INTO votes(voter_id, candidate_id, encrypted_vote) VALUES(%s,%s,%s)",
                       (voter_id, candidate_id, encrypted))

        # 2. Vote count +1 karo - YAHI LINE FIX
        cursor.execute("UPDATE candidates SET vote_count = vote_count + 1 WHERE id=%s", (candidate_id,))
        # AGAR TUMHARI TABLE ME 'candidate_id' hai TO UPAR WALI LINE KO YE KAR DO:
        # cursor.execute("UPDATE candidates SET vote_count = vote_count + 1 WHERE candidate_id=%s", (candidate_id,))

        # 3. Voter ko voted mark karo
        cursor.execute("UPDATE voters SET has_voted=1 WHERE id=%s", (voter_id,))
        db.commit()
        session.clear()
        flash("Vote Submitted Successfully!")
        return redirect('/')
    except Exception as e:
        db.rollback()
        flash(f"Error: {e}")
        return redirect('/vote')

# 7. ADMIN LOGIN
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['username']=='admin' and request.form['password']=='admin123':
            session['admin'] = True
            return redirect('/dashboard')
        flash("Wrong Admin Credentials")
    return render_template('admin_login.html')

# 8. ADMIN DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/admin')
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    cursor.execute("SELECT id, name, aadhar, mobile, has_voted FROM voters")
    voters = cursor.fetchall()
    return render_template('admin_dashboard.html', candidates=candidates, voters=voters)

# 9. ADD CANDIDATE
@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    cursor.execute("INSERT INTO candidates(name, party) VALUES(%s,%s)",
                   (request.form['name'], request.form['party']))
    db.commit()
    return redirect('/dashboard')

# 10. RESULT
@app.route('/result')
def result():
    cursor.execute("SELECT name, party, vote_count FROM candidates ORDER BY vote_count DESC")
    results = cursor.fetchall()
    return render_template('result.html', results=results)

# 11. LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# NGROK START
if __name__ == '__main__':
    from pyngrok import ngrok
    ngrok.set_auth_token("3HSdNneBJPiBzxdiUJeWFea3urT_82pKJoQbvZGhiY1veye2z")
    public_url = ngrok.connect(5000)
    print("\n=====================================")
    print(" PUBLIC LINK:", public_url)
    print("=====================================\n")
    app.run(host='0.0.0.0', port=5000)