import streamlit as st

# Set the page title and layout
st.set_page_config(page_title="Prototype Phase Completion", layout="wide")

# Custom CSS to mimic some of the HTML styling
st.markdown("""
    <style>
        .big-font {
            font-family: Arial, sans-serif;
            font-size: 20px;
            text-align: center;
        }
        .thank-you-note {
            padding: 15px;
            background-color: #f2f2f2;
            color: black;
            margin: 20px 0;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

# Header section
st.markdown('<h1 style="color: white; background-color: #35424a; padding: 30px; text-align: center;">Volvo Trucks AI-powered Video Generator</h1>', unsafe_allow_html=True)

# Navigation links (Streamlit does not support direct HTML links in the sidebar, so markdown is used)
st.sidebar.markdown('[Home](/)')
st.sidebar.markdown('[Generative AI Playground](https://volvogroup.sharepoint.com/sites/coll-vt-c4a-public/SitePages/Volvo-Trucks-Generative-AI-Playground.aspx)')
st.sidebar.markdown('[Contact](https://volvogroup.sharepoint.com/sites/coll-vt-c4a-public/SitePages/Get-in-Touch.aspx)')

# Main content
st.markdown('<div class="thank-you-note">', unsafe_allow_html=True)
st.markdown('## Thank You for Participating in Our Prototype Phase!', unsafe_allow_html=True)
st.markdown("""
    Together we have produced more than 350 videos using this prototype and we are grateful for the immense number of feedback submissions we have received. Your contributions have been invaluable in shaping our web app's future.

    As this prototype phase has concluded, we will be taking down the app to analyze your feedback and implement improvements for future production-grade application.

    If you see the potential for a similar application in your team or department at Volvo Trucks, we encourage you to get in touch with us. Our team is ready to work together to identify tailored solutions that meet your specific needs.

    For more information about the prototype and its journey, visit [Exploring Generative AI micro-training generation](https://volvogroup.sharepoint.com/sites/coll-vt-c4a-public/SitePages/Exploring-the.aspx).

    **We look forward to continuing our journey together and bringing more innovative solutions like this to production at Volvo Trucks!**
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Adjust the layout as needed to fit Streamlit's limitations and your specific requirements.
