"""Octa Launcher — Supabase client (minimal, read-only user auth)."""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def _client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def db() -> Client:
    return _client()


def get_all_partners() -> list:
    try:
        resp = db().table("partners").select("full_name") \
                   .order("full_name").execute()
        return resp.data or []
    except Exception:
        return []
