import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader # Import ImageReader for PDF images
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io
import streamlit.components.v1 as components # Import components for HTML injection
import os # Import os module to handle file paths
import pandas as pd # Import pandas for reading Excel/CSV

# --- Image Paths (Only LekaLink Logo for PDF remains) ---
LEKALINK_LOGO_PATH = os.path.join("assets", "LL_Stacked_Gradient.png") # Path to the LekaLink logo

# --- Pricing Configuration (Default values) ---
# These default rates will be used if CSV loading fails or if CSV is not found
DEFAULT_VM_RATE = 864.35
DEFAULT_STORAGE_RATE_PER_TB = 870.40
DEFAULT_BANDWIDTH_RATE_PER_MBPS = 7.50 # Changed from 2.50 to 7.50

# Initialize rates with default values. These will be updated if CSV loads successfully.
VM_RATE = DEFAULT_VM_RATE
STORAGE_RATE_PER_TB = DEFAULT_STORAGE_RATE_PER_TB
BANDWIDTH_RATE_PER_MBPS = DEFAULT_BANDWIDTH_RATE_PER_MBPS


# --- Pricing Configuration (Dynamically loaded from CSV) ---
PRICE_SHEET_PATH = os.path.join("assets", "Leka Link_Channel Partner_VDC Calculator.xlsx - VDC Calculation.csv")

try:
    # Check if assets directory exists
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        st.error(f"Error: The '{assets_dir}' directory was not found. Please ensure your CSV file is inside a folder named '{assets_dir}' in the same directory as your app.py.")
        # Raise an error to skip further CSV loading attempts in this block
        raise FileNotFoundError(f"Directory '{assets_dir}' not found.") 

    # Check if the CSV file exists within the assets directory
    if not os.path.exists(PRICE_SHEET_PATH):
        st.error(f"Error: The price sheet CSV file was not found at '{PRICE_SHEET_PATH}'. Please ensure the file name is exactly 'Leka Link_Channel Partner_VDC Calculator.xlsx - VDC Calculation.csv' and it's inside the 'assets' folder.")
        # Raise an error to skip further CSV loading attempts in this block
        raise FileNotFoundError(f"File '{PRICE_SHEET_PATH}' not found.")

    # If both exist, proceed with reading the CSV
    price_df = pd.read_csv(
        PRICE_SHEET_PATH,
        header=4,
        encoding='latin-1',
        on_bad_lines='skip', # Skip lines that cause parsing errors
        engine='python' # Use the Python parsing engine for more flexibility
    )
    
    # Strip whitespace from column names to handle potential inconsistencies
    price_df.columns = price_df.columns.str.strip()

    # Explicitly convert 'Unit Monthly' column to numeric, coercing errors to NaN
    # Then fill NaN values with the default rates to ensure numerical operations
    price_df['Unit Monthly'] = pd.to_numeric(price_df['Unit Monthly'], errors='coerce')

    # Extract prices from the 'Unit Monthly' column
    vm_row = price_df.loc[price_df['Description'] == 'Virtual Data Centre(Allocation Resource Pool)']
    if not vm_row.empty and not pd.isna(vm_row['Unit Monthly'].iloc[0]):
        VM_RATE = vm_row['Unit Monthly'].iloc[0]
    else:
        # Fallback to default if row not found or value is NaN
        VM_RATE = DEFAULT_VM_RATE
        print("Warning: Could not find 'Virtual Data Centre(Allocation Resource Pool)' or its price in price sheet. Using default VM rate.")


    storage_row = price_df.loc[price_df['Description'] == 'vStorage - NVME/SSD']
    if not storage_row.empty and not pd.isna(storage_row['Unit Monthly'].iloc[0]):
        STORAGE_RATE_PER_TB = storage_row['Unit Monthly'].iloc[0] * 1024 # CSV has price per GB, convert to per TB
    else:
        # Fallback to default if row not found or value is NaN
        STORAGE_RATE_PER_TB = DEFAULT_STORAGE_RATE_PER_TB
        print("Warning: Could not find 'vStorage - NVME/SSD' or its price in price sheet. Using default Storage rate.")

    # Removed st.success message
    # st.success("Pricing rates successfully loaded from CSV!")

except FileNotFoundError as e:
    # The specific error messages are already printed above by st.error
    print(f"Caught FileNotFoundError: {e}. Using default pricing rates.")
except KeyError as e:
    st.error(f"Error reading column from price sheet: {e}. Ensure 'Description' and 'Unit Monthly' columns exist and are correctly formatted. Using default pricing rates.")
except Exception as e:
    st.error(f"An unexpected error occurred while loading prices from CSV: {e}. Using default pricing rates.")


# --- Custom CSS for Branding ---
# Using Inter font from Google Fonts, LekaLink colors, and responsive design
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

/* Apply font family globally */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

/* Force all h1, h2, h3, p, and label elements to the desired purple color */
h1, h2, h3, p, label {
    color: #511281 !important;
}

/* Target Streamlit's main content div and its children to force color */
div[data-testid="stAppViewContainer"] * {
    color: #511281 !important;
}

/* Apply border and rounded corners to the main app container */
.stApp {
    background: linear-gradient(180deg, #f0f2f6 0%, #e0e5ec 100%); /* Light gradient background */
    padding: 2rem; /* Adjusted padding to ensure content is inside border */
    border: 3px solid #511281 !important; /* Added !important to force border color */
    border-radius: 20px; /* Rounded corners */
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* Added a subtle shadow to the border */
}

/* Header Gradient */
.header-section {
    background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%); /* Purple to blue gradient */
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.header-section h1 {
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.header-section p {
    color: rgba(255, 255, 255, 0.8) !important; /* Keep this white for contrast in the header, with !important */
    font-size: 1.1rem;
}

/* Input Card Styling */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: 10px;
    border: 1px solid #ddd;
    padding: 0.75rem 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* Button Styling */
.stButton > button {
    background-color: #16a34a; /* LekaLink Green */
    color: white;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 10px;
    border: none;
    transition: background-color 0.3s ease, transform 0.2s ease;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.stButton > button:hover {
    background-color: #128a3a; /* Darker green on hover */
    transform: translateY(-2px);
}
.stButton > button:active {
    transform: translateY(0);
}

/* Results Card Styling */
.results-card {
    background: linear-gradient(135deg, #e0e5ec 0%, #f0f2f6 100%); /* Light gradient */
    border-radius: 15px;
    padding: 2rem;
    margin-top: 2rem;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    border: 1px solid #d0d5db;
}
.results-card p {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}
.results-card .savings-positive {
    color: #16a34a !important; /* LekaLink Green for positive savings, with !important */
    font-weight: 700;
    font-size: 1.3rem;
}
.results-card .savings-negative {
    color: #e74c3c !important; /* Red for negative savings/increase, with !important */
    font-weight: 700;
    font-size: 1.3rem;
}

/* Remove Streamlit header/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
"""

# Inject custom CSS using st.components.v1.html
components.html(f"<style>{CUSTOM_CSS}</style>", height=0, width=0)

# --- Helper Functions ---
def create_pdf(data):
    """Generates a PDF quote from the calculated data."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Define purple color for headings
    PURPLE_RGB = (0.3176, 0.0706, 0.5059) # RGB for #511281

    # --- Add LekaLink Logo to PDF (Top Center) ---
    try:
        if os.path.exists(LEKALINK_LOGO_PATH):
            logo = ImageReader(LEKALINK_LOGO_PATH)
            img_width, img_height = logo.getSize()
            
            # Desired width for the logo on PDF (e.g., 1.5 inches)
            logo_display_width = 1.5 * inch
            logo_display_height = logo_display_width * (img_height / img_width)

            # Calculate x position for centering
            x_position_logo = (width - logo_display_width) / 2
            # Position at the top with some margin
            y_position_logo = height - logo_display_height - 0.5 * inch
            c.drawImage(logo, x_position_logo, y_position_logo, width=logo_display_width, height=logo_display_height)
        else:
            st.warning(f"LekaLink logo not found at {LEKALINK_LOGO_PATH}. Skipping logo in PDF.")
    except Exception as e:
        st.error(f"Error loading LekaLink logo for PDF: {e}")
    # --- End LekaLink Logo ---

    # Adjust starting y_position for text based on logo presence
    y_position = height - 1.5 * inch if not os.path.exists(LEKALINK_LOGO_PATH) else y_position_logo - 0.5 * inch


    # Title
    c.setFont('Helvetica-Bold', 24)
    c.setFillColorRGB(*PURPLE_RGB) # Set title color to purple
    c.drawString(inch, y_position, "LekaLink Cloud Cost Quote")
    y_position -= 0.5 * inch # Move down after title

    # Company and Contact Info
    c.setFillColorRGB(*PURPLE_RGB) # Set heading color to purple
    c.setFont('Helvetica-Bold', 14)
    c.drawString(inch, y_position, "Client Information:")
    y_position -= 0.3 * inch
    c.setFillColorRGB(0, 0, 0) # Set text color to black
    c.setFont('Helvetica', 12)
    c.drawString(inch, y_position, f"Company: {data['company_name']}")
    y_position -= 0.25 * inch
    c.drawString(inch, y_position, f"Contact: {data['contact_name']} ({data['job_title']})")
    y_position -= 0.25 * inch
    c.drawString(inch, y_position, f"Email: {data['email']}")
    y_position -= 0.25 * inch
    c.drawString(inch, y_position, f"Phone: {data['phone']}")

    y_position -= 0.5 * inch

    # Current Costs
    c.setFillColorRGB(*PURPLE_RGB) # Set heading color to purple
    c.setFont('Helvetica-Bold', 14)
    c.drawString(inch, y_position, "Current Cloud Costs:")
    y_position -= 0.3 * inch
    c.setFillColorRGB(0, 0, 0) # Set text color to black
    c.setFont('Helvetica', 12)
    c.drawString(inch, y_position, f"Monthly Cost: R{data['current_cost']:.2f}")

    y_position -= 0.5 * inch

    # LekaLink Estimated Costs
    c.setFillColorRGB(*PURPLE_RGB) # Set heading color to purple
    c.setFont('Helvetica-Bold', 14)
    c.drawString(inch, y_position, "LekaLink Estimated Costs:")
    y_position -= 0.3 * inch
    c.setFillColorRGB(0, 0, 0) # Set text color to black
    c.setFont('Helvetica', 12)
    
    # Display only estimated totals per item
    c.drawString(inch, y_position, f"Virtual Machines: R{data['vms'] * data['vm_rate']:.2f}")
    y_position -= 0.25 * inch
    c.drawString(inch, y_position, f"Storage: R{data['storage'] * data['storage_rate_per_tb']:.2f}")
    y_position -= 0.25 * inch
    c.drawString(inch, y_position, f"Bandwidth: R{data['bandwidth'] * data['bandwidth_rate_per_mbps']:.2f}")
    y_position -= 0.25 * inch
    c.setFont('Helvetica-Bold', 12)
    c.drawString(inch, y_position, f"Total LekaLink Estimated Cost: R{data['lekalink_cost']:.2f}")

    y_position -= 0.5 * inch

    # Savings
    c.setFillColorRGB(*PURPLE_RGB) # Set heading color to purple
    c.setFont('Helvetica-Bold', 14)
    c.drawString(inch, y_position, "Potential Savings:")
    y_position -= 0.3 * inch
    c.setFillColorRGB(0, 0, 0) # Set text color to black
    c.setFont('Helvetica', 12)
    if data['monthly_savings'] >= 0:
        c.setFillColorRGB(0.08, 0.64, 0.29) # LekaLink Green
        c.drawString(inch, y_position, f"Monthly Savings: R{data['monthly_savings']:.2f}")
        y_position -= 0.25 * inch
        c.drawString(inch, y_position, f"Percentage Savings: {data['percentage_savings']:.2f}%")
    else:
        c.setFillColorRGB(0.91, 0.30, 0.24) # Red
        c.drawString(inch, y_position, f"Monthly Increase: R{-data['monthly_savings']:.2f}")
        y_position -= 0.25 * inch
        c.drawString(inch, y_position, f"Percentage Increase: {-data['percentage_savings']:.2f}%")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def send_email(recipient_email, subject, body, attachment_data=None, attachment_filename=None):
    """Sends an email with an optional attachment."""
    # --- IMPORTANT: Replace with your actual email credentials and SMTP server ---
    # For Microsoft 365/Outlook, use smtp.office365.com and port 587 (TLS)
    SENDER_EMAIL = "adriennek@intellicomms.co.za"  # Fixed sender email
    SENDER_PASSWORD = "1118@Jun32250AK" # Fixed sender password
    SMTP_SERVER = "smtp.office365.com" # Microsoft 365 SMTP server
    SMTP_PORT = 587
    # --- END IMPORTANT ---

    # Removed the check for YOUR_EMAIL_ADDRESS and YOUR_EMAIL_APP_PASSWORD as they are now fixed
    # if SENDER_EMAIL == "YOUR_EMAIL_ADDRESS" or SENDER_PASSWORD == "YOUR_EMAIL_APP_PASSWORD":
    #     st.error("Email sending is not configured. Please replace 'YOUR_EMAIL_ADDRESS' and 'YOUR_EMAIL_APP_PASSWORD' in the code.")
    #     return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_data and attachment_filename:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {attachment_filename}")
            msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- Input Validation Function ---
def validate_inputs(company_name, contact_name, job_title, email, phone):
    """Validates that all required contact information fields are not empty."""
    if not company_name:
        st.error("Company Name is required.")
        return False
    if not contact_name:
        st.error("Contact Name is required.")
        return False
    if not job_title:
        st.error("Job Title is required.")
        return False
    if not email:
        st.error("Email is required.")
        return False
    if not phone:
        st.error("Phone Number is required.")
        return False
    return True

# --- Streamlit App Layout ---

# Removed the h1 heading and centered the paragraph
st.markdown('<div class="header-section"><p>Estimate your savings when you switch to LekaLink Cloud Services!</p></div>', unsafe_allow_html=True)

# Create two main columns for the input sections
left_column, right_column = st.columns(2)

with left_column:
    st.subheader("Your Current Cloud Usage")
    vms = st.number_input("Number of Virtual Machines", min_value=0, value=0, step=1, key="vms")
    storage = st.number_input("Storage (TB)", min_value=0.0, value=0.0, step=0.1, format="%.1f", key="storage")
    bandwidth = st.number_input("Bandwidth (Mbps)", min_value=0.0, value=0.0, step=1.0, format="%.1f", key="bandwidth")
    current_cost = st.number_input("Current Monthly Cloud Cost (R)", min_value=0.0, value=0.0, step=100.0, format="%.2f", key="current_cost")

with right_column:
    st.subheader("Your Contact Information")
    company_name = st.text_input("Company Name", key="company_name")
    contact_name = st.text_input("Contact Name", key="contact_name")
    job_title = st.text_input("Job Title", key="job_title")
    email = st.text_input("Email", key="email")
    phone = st.text_input("Phone Number", key="phone")

# Button and results will appear below the two columns
if st.button("Save me Money"):
    # Perform validation before calculations
    if validate_inputs(company_name, contact_name, job_title, email, phone):
        # --- Calculation Logic ---
        # Use the determined rates (either from CSV or default if CSV fails)
        lekalink_cost = (vms * VM_RATE) + (storage * STORAGE_RATE_PER_TB) + (bandwidth * BANDWIDTH_RATE_PER_MBPS)
        monthly_savings = current_cost - lekalink_cost
        percentage_savings = (monthly_savings / current_cost * 100) if current_cost != 0 else 0

        st.markdown('<div class="results-card">', unsafe_allow_html=True)
        st.write("### Your Estimated Savings with LekaLink")
        st.write(f"**LekaLink Estimated Monthly Cost:** R{lekalink_cost:.2f}")

        if monthly_savings >= 0:
            st.markdown(f'<p class="savings-positive">**Monthly Savings:** R{monthly_savings:.2f}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="savings-positive">**Percentage Savings:** {percentage_savings:.2f}%</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="savings-negative">**Monthly Increase:** R{-monthly_savings:.2f}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="savings-negative">**Percentage Increase:** {-percentage_savings:.2f}%</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Prepare data for PDF
        quote_data = {
            "company_name": company_name,
            "contact_name": contact_name,
            "job_title": job_title,
            "email": email,
            "phone": phone,
            "vms": vms,
            "storage": storage,
            "bandwidth": bandwidth,
            "current_cost": current_cost,
            "lekalink_cost": lekalink_cost,
            "monthly_savings": monthly_savings,
            "percentage_savings": percentage_savings,
            "vm_rate": VM_RATE, # Pass the actual rates used to PDF function
            "storage_rate_per_tb": STORAGE_RATE_PER_TB,
            "bandwidth_rate_per_mbps": BANDWIDTH_RATE_PER_MBPS
        }

        pdf_output = create_pdf(quote_data)

        st.download_button(
            label="Download Quote as PDF",
            data=pdf_output,
            file_name=f"LekaLink_Cloud_Quote_{company_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

        # Automatically send email to sales team
        sales_email = "adriennek@intellicomms.co.za"
        email_subject = f"New LekaLink Cloud Cost Quote for {company_name}"
        email_body = f"""
A new LekaLink Cloud Cost Quote has been generated for:

Company: {company_name}
Contact: {contact_name} ({job_title})
Email: {email}
Phone: {phone}

Current Monthly Cost: R{current_cost:.2f}
LekaLink Estimated Monthly Cost: R{lekalink_cost:.2f}

"""
        if monthly_savings >= 0:
            email_body += f"Potential Monthly Savings: R{monthly_savings:.2f}\n"
            email_body += f"Potential Percentage Savings: {percentage_savings:.2f}%\n"
        else:
            email_body += f"Monthly Cost Increase: R{-monthly_savings:.2f}\n"
            email_body += f"Percentage Cost Increase: {-percentage_savings:.2f}%\n"

        email_body += """
Please find the detailed quote attached.
"""
        if send_email(sales_email, email_subject, email_body, pdf_output, f"LekaLink_Cloud_Quote_{company_name.replace(' ', '_')}.pdf"):
            st.success(f"Quote generated and sent to the sales team at {sales_email}!")
        else:
            st.error("Failed to send the quote to the sales team. Please check the console for errors.")
    else:
        # Validation failed, error messages are already displayed by validate_inputs
        pass
