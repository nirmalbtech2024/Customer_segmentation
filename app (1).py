import streamlit as st
import json, os
import pandas as pd
import numpy as np
import plotly.express as px
import bcrypt
import requests

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# ===== CONFIG =====
st.set_page_config(page_title="AI SaaS Ultimate", layout="wide")

DB_FILE = "users.json"
DATA_FOLDER = "user_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# ===== SESSION =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = None
    st.session_state.role = None
    st.session_state.theme = "Dark"
    st.session_state.chat = []
    st.session_state.history = []

# ===== SECURITY =====
def hash_pass(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_pass(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        # fallback for old/plain passwords
        return password == hashed

# ===== USER =====
def load_users():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

def user_file():
    return os.path.join(DATA_FOLDER, f"{st.session_state.email}.csv")

def profile_pic():
    return os.path.join(DATA_FOLDER, f"{st.session_state.email}_profile.png")

# ===== UI HELPERS =====
def notify(msg, type="success"):
    if type == "success":
        st.success(msg)
    elif type == "error":
        st.error(msg)
    else:
        st.info(msg)

def load_lottie(url):
    return requests.get(url).json()

# ===== THEME =====
dark_mode = st.sidebar.toggle("🌙 Dark Mode", True)
if dark_mode:
    st.markdown("<style>body{background:#0e1117;color:white;}</style>", unsafe_allow_html=True)

# ===== AUTH =====
def login():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        if email in users:
            stored_pass = users[email]["password"]

            if check_pass(password, stored_pass):

                # 🔥 upgrade old password to bcrypt
                if not stored_pass.startswith("$2b$"):
                    users[email]["password"] = hash_pass(password)
                    save_users(users)

                st.session_state.logged_in = True
                st.session_state.email = email
                st.session_state.role = users[email].get("role", "user")
                notify("Login successful")
            else:
                notify("Invalid login", "error")
        else:
            notify("User not found", "error")

def signup():
    st.title("✨ Signup")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        users = load_users()
        if email in users:
            notify("User exists", "error")
        else:
            users[email] = {
                "password": hash_pass(password),
                "role": "user",
                "name": "",
                "bio": ""
            }
            save_users(users)
            notify("Account created")

# ===== HOME =====
def home():
    st.title("🚀 AI SaaS Platform")

    st.session_state.history.append("Visited Home")

    c1, c2, c3 = st.columns(3)
    c1.metric("Users", len(load_users()))
    c2.metric("Datasets", len(os.listdir(DATA_FOLDER)))
    c3.metric("AI Tools", 5)

    st.info("Upload, Analyze, and get AI insights")

# ===== DATA =====
def data_manager():
    file = st.file_uploader("Upload CSV/Image", type=["csv", "png", "jpg"])

    if file:
        notify("File uploaded successfully")

        if file.type == "text/csv":
            df = pd.read_csv(file)
            df.to_csv(user_file(), index=False)
            st.dataframe(df)
            return df
        else:
            st.image(file)

    if os.path.exists(user_file()):
        df = pd.read_csv(user_file())
        return df
    return None

# ===== DASHBOARD =====
def dashboard():
    st.title("📊 Smart Dashboard")

    st.session_state.history.append("Visited Dashboard")

    df = data_manager()

    if df is None:
        df = pd.DataFrame({
            "Age": np.random.randint(18, 60, 200),
            "Income": np.random.randint(20000, 120000, 200),
            "Score": np.random.randint(1, 100, 200)
        })

    # Search
    search = st.text_input("🔍 Search")
    if search:
        df = df[df.astype(str).apply(lambda r: r.str.contains(search).any(), axis=1)]

    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(df))
    c2.metric("Columns", len(df.columns))
    c3.metric("Missing", int(df.isnull().sum().sum()))

    st.dataframe(df)

    # Clustering
    if st.checkbox("Enable Clustering"):
        num = df.select_dtypes(include=np.number)
        if len(num.columns) >= 2:
            k = st.slider("Clusters", 2, 10, 3)
            scaled = StandardScaler().fit_transform(num)
            df["Cluster"] = KMeans(n_clusters=k).fit_predict(scaled)
            st.write(df.groupby("Cluster").mean())

    # Download
    st.download_button("⬇ Download CSV", df.to_csv(index=False), "data.csv")

# ===== CHATBOT =====
def chatbot():
    st.title("🤖 Chatbot")

    user_input = st.text_input("Ask something")

    if st.button("Send"):
        reply = user_input[::-1]
        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("Bot", reply))

    for sender, msg in st.session_state.chat:
        st.write(f"**{sender}:** {msg}")

# ===== SETTINGS =====
def settings():
    st.title("⚙️ Settings")

    users = load_users()
    user = users.get(st.session_state.email, {})

    tab = st.radio("Menu", ["Profile", "Security", "Preferences", "Data"])

    if tab == "Profile":
        name = st.text_input("Name", user.get("name", ""))
        bio = st.text_area("Bio", user.get("bio", ""))

        pic = st.file_uploader("Profile Pic", type=["png", "jpg"])
        if pic:
            with open(profile_pic(), "wb") as f:
                f.write(pic.getbuffer())
            st.image(profile_pic(), width=100)

        if st.button("Save"):
            users[st.session_state.email]["name"] = name
            users[st.session_state.email]["bio"] = bio
            save_users(users)
            notify("Profile updated")

    elif tab == "Security":
        new = st.text_input("New Password", type="password")
        if st.button("Change"):
            users[st.session_state.email]["password"] = hash_pass(new)
            save_users(users)
            notify("Password updated")

    elif tab == "Preferences":
        theme = st.selectbox("Theme", ["Dark", "Light"])
        st.session_state.theme = theme

    elif tab == "Data":
        if st.button("Delete My Data"):
            if os.path.exists(user_file()):
                os.remove(user_file())
                notify("Data deleted")

# ===== FEEDBACK =====
def feedback():
    st.title("⭐ Feedback")

    rating = st.slider("Rate", 1, 5)
    comment = st.text_area("Comment")

    if st.button("Submit"):
        with open("feedback.txt", "a") as f:
            f.write(f"{rating}-{comment}\n")
        notify("Thanks for feedback ❤️")

# ===== APP =====
def app():
    with st.sidebar:
        choice = option_menu(
            "AI SaaS",
            ["Home", "Dashboard", "Chatbot", "Settings", "Feedback"],
            icons=["house", "bar-chart", "robot", "gear", "star"]
        )

    if choice == "Home":
        home()
    elif choice == "Dashboard":
        dashboard()
    elif choice == "Chatbot":
        chatbot()
    elif choice == "Settings":
        settings()
    elif choice == "Feedback":
        feedback()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False

# ===== MAIN =====
if st.session_state.logged_in:
    app()
else:
    page = st.sidebar.selectbox("Menu", ["Login", "Signup"])
    if page == "Login":
        login()
    else:
        signup()