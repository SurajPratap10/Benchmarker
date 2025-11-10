"""
Authentication module for Benchmarker
"""
import streamlit as st
from typing import Optional, Tuple
from datetime import datetime, timedelta
from user_database import user_db

class AuthManager:
    """Manages authentication for the application"""
    
    def __init__(self):
        # Session timeout in minutes
        try:
            self.session_timeout = int(st.secrets.get("SESSION_TIMEOUT_MINUTES", 60))
        except:
            self.session_timeout = 60  # Default 60 minutes
    
    def register(self, username: str, password: str, confirm_password: str, email: Optional[str] = None) -> Tuple[bool, str]:
        """
        Register a new user
        Returns (success, message)
        """
        if not username or not password:
            return False, "Username and password are required"
        
        if password != confirm_password:
            return False, "Passwords do not match"
        
        # Create user in database
        success, message = user_db.create_user(username, password, email)
        return success, message
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Attempt to log in with username and password
        Returns (success, message)
        """
        if not username or not password:
            return False, "Please enter both username and password"
        
        # Verify with database
        success, user_data = user_db.verify_user(username, password)
        
        if success and user_data:
            # Set session state
            st.session_state.authenticated = True
            st.session_state.username = user_data["username"]
            st.session_state.user_id = user_data["id"]
            st.session_state.user_email = user_data.get("email")
            st.session_state.login_time = datetime.now()
            return True, "Login successful"
        else:
            return False, "Invalid username or password"
    
    def logout(self):
        """Log out the current user"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.login_time = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated and session is valid"""
        if not st.session_state.get("authenticated", False):
            return False
        
        # Check session timeout
        login_time = st.session_state.get("login_time")
        if login_time:
            elapsed = datetime.now() - login_time
            if elapsed > timedelta(minutes=self.session_timeout):
                self.logout()
                return False
        
        return True
    
    def get_username(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.get("username")
    
    def get_user_id(self) -> Optional[int]:
        """Get current user ID"""
        return st.session_state.get("user_id")
    
    def require_auth(self):
        """Decorator/function to require authentication"""
        if not self.is_authenticated():
            self.show_login_page()
            st.stop()
    
    def show_login_page(self):
        """Display login/register page"""
        
        # Initialize page mode
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"
        
        st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #0A7C7E 0%, #1A1A1A 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            font-weight: 700;
            color: white;
            margin: 0 auto 1rem auto;
        }
        .login-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: #1A1A1A;
            margin: 0;
        }
        .login-subtitle {
            color: #6B6B6B;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        </style>
        <div class="login-container">
            <div class="login-header">
                <div class="login-logo">B</div>
                <div class="login-title"><span style="color: #0A7C7E;">Bench</span>marker</div>
                <div class="login-subtitle">TTS Benchmarking Platform</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Toggle between login and register
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            
            with tab1:
                # LOGIN FORM
                st.markdown("Welcome back! Please sign in to continue.")
                
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter username", key="login_username")
                    password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
                    
                    submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                    
                    if submit:
                        success, message = self.login(username, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            with tab2:
                # REGISTER FORM
                st.markdown("Create a new account to get started.")
                
                with st.form("register_form"):
                    new_username = st.text_input("Username", placeholder="Choose a username (min 3 characters)", key="reg_username")
                    new_email = st.text_input("Email (optional)", placeholder="your@email.com", key="reg_email")
                    new_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 characters)", key="reg_password")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="reg_confirm")
                    
                    register_submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                    
                    if register_submit:
                        success, message = self.register(new_username, new_password, confirm_password, new_email)
                        if success:
                            st.success(f"{message}! Please sign in.")
                            st.session_state.auth_mode = "login"
                        else:
                            st.error(message)
            
            st.markdown("---")
            total_users = user_db.get_total_users()
            st.markdown(f"""
            <div style="text-align: center; color: #6B6B6B; font-size: 0.85rem;">
                <p>👥 <strong>{total_users}</strong> users registered</p>
            </div>
            """, unsafe_allow_html=True)

# Initialize global auth manager
auth_manager = AuthManager()

