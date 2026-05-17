from __future__ import annotations

import streamlit as st


dashboard = st.Page("pages/dashboard.py", title="Dashboard", url_path="", default=True)
admin = st.Page("pages/admin.py", title="Admin / PDF Audit", url_path="admin")

navigation = st.navigation([dashboard, admin], position="hidden")
navigation.run()
