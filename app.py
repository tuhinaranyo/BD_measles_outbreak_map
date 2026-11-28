"""This dashboard is closed. It moved to https://www.tuhinhasan.com/measles-alert/

The old dashboard code (pages/, measles_dashboard/) is kept for reference but no longer runs.
"""
from __future__ import annotations

import streamlit as st

MEASLES = "https://www.tuhinhasan.com/measles-alert/"
DENGUE = "https://www.tuhinhasan.com/dengue-alert/"


def moved() -> None:
    st.set_page_config(page_title="হাম আপডেট এখন নতুন ঠিকানায়")
    st.title("হাম আপডেট এখন নতুন ঠিকানায়")
    st.warning("এই পুরোনো ড্যাশবোর্ড বন্ধ করা হয়েছে। এখানে আর নতুন তথ্য আসবে না।")
    st.markdown("আগের স্ক্রিনশট বা সংখ্যার বদলে নতুন পেজের সংখ্যা দেখুন।")
    st.link_button("হাম আপডেট দেখুন", MEASLES, type="primary", use_container_width=True)
    st.link_button("ডেঙ্গু আপডেট দেখুন", DENGUE, use_container_width=True)
    st.markdown(f"লিংক: [{MEASLES}]({MEASLES})")


# Old addresses (the home page and /admin) both show the notice.
st.navigation(
    [st.Page(moved, title="Moved", default=True), st.Page(moved, title="Moved", url_path="admin")],
    position="hidden",
).run()
