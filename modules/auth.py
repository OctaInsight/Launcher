"""Octa Launcher — Auth (full: login, register, password reset, SSO)."""
import bcrypt
import streamlit as st
from datetime import datetime, timezone
from modules.database import db

APP_NAME = "launcher"


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ── User lookups ──────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    try:
        resp = db().table("octa_users").select("*") \
                   .eq("email", email.strip().lower()).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def get_user_by_username(username: str) -> dict | None:
    try:
        resp = db().table("octa_users").select("*") \
                   .eq("username", username.strip()).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(email: str, username: str, first_name: str,
                  last_name: str, password: str,
                  organisation: str = "") -> tuple:
    if len(password) < 8:
        return False, "Password must be at least 8 characters.", None
    if "@" not in email:
        return False, "Invalid email address.", None
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters.", None
    if get_user_by_email(email):
        return False, "This email is already registered.", None
    if get_user_by_username(username):
        return False, "This username is already taken.", None
    try:
        resp = db().table("octa_users").insert({
            "email":         email.strip().lower(),
            "username":      username.strip(),
            "first_name":    first_name.strip(),
            "last_name":     last_name.strip(),
            "password_hash": hash_password(password),
            "status":        "pending",
            "apps_access":   [],
            "role":          "user",
            "organisation":  organisation.strip(),
        }).execute()
        user = resp.data[0] if resp.data else None
        return True, "Registration submitted.", user
    except Exception as e:
        return False, f"Registration failed: {e}", None


# ── Password reset request ────────────────────────────────────────────────────

def request_password_reset(email: str) -> tuple:
    user = get_user_by_email(email)
    if not user:
        return True, ("Reset request submitted. If your email is registered, "
                      "an admin will contact you with a temporary password.")
    try:
        existing = db().table("password_reset_requests").select("id") \
                       .eq("user_id", user["id"]).eq("status","pending").execute()
        if existing.data:
            return True, "A reset request is already pending. Contact your admin."
        db().table("password_reset_requests").insert({
            "user_id": user["id"],
            "status":  "pending",
        }).execute()
        return True, ("✅ Reset request submitted. An admin will provide "
                      "you with a temporary password via phone or personal email.")
    except Exception as e:
        return False, f"Error: {e}"


# ── Login ─────────────────────────────────────────────────────────────────────

def _update_last_login(user_id: int):
    try:
        db().table("octa_users") \
            .update({"last_login": datetime.now(timezone.utc).isoformat()}) \
            .eq("id", user_id).execute()
    except Exception:
        pass


# ── Session ───────────────────────────────────────────────────────────────────

def set_session(user: dict):
    apps = user.get("apps_access") or []
    if isinstance(apps, str):
        import json
        try:    apps = json.loads(apps)
        except: apps = []
    st.session_state.authenticated        = True
    st.session_state.user_id              = user["id"]
    st.session_state.username             = user.get("username","")
    st.session_state.first_name           = user.get("first_name","")
    st.session_state.last_name            = user.get("last_name","")
    st.session_state.email                = user.get("email","")
    st.session_state.role                 = user.get("role","user")
    st.session_state.organisation         = user.get("organisation","")
    st.session_state.apps_access          = apps
    st.session_state.force_password_change= bool(user.get("force_password_change"))


def clear_session():
    for k in ["authenticated","user_id","username","first_name","last_name",
              "email","role","organisation","apps_access","sso_token",
              "force_password_change"]:
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def needs_password_change() -> bool:
    return bool(st.session_state.get("force_password_change"))
