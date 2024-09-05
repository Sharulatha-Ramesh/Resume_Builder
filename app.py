# import tempfile
# from flask import Flask, render_template, request, send_file
# import boto3
# from botocore.exceptions import NoCredentialsError
import os
import tempfile
from xhtml2pdf import pisa
from flask import Flask, render_template, request, send_file
import boto3
from botocore.exceptions import NoCredentialsError
from docx import Document
from html2docx import html2docx
app = Flask(__name__)

# AWS credentials
AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
AWS_REGION = 'us-east-1'
S3_BUCKET_NAME = 'urahs-bucket'

# Initialize S3 client
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

# Define the route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Define the route for form submission


@app.route('/submit', methods=['POST'])
def submit():
    data = request.form

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resume Form</title>
        <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
        <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
        <style>
            ul {{
                list-style-type: disc;
                margin-left: 20px;
            }}
            .section-title {{
                font-weight: bold;
            }}
            .icon {{
                margin-right: 5px;
            }}
            .black-line {{
                border-top: 1px solid black;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <h1 class="section-title" align="center">{data['name']}</h1>
        <p align="center">
            <i class="fas fa-envelope icon"></i>&nbsp;{data.get('email', '')}&nbsp;&nbsp;
            <i class="fas fa-phone icon"></i>&nbsp;{data.get('phone', '')}&nbsp;&nbsp;
            <i class="fas fa-map-marker-alt icon"></i>&nbsp;{data.get('address', '')}&nbsp;&nbsp;
            <i class="fab fa-linkedin icon"></i>&nbsp;{data.get('linkedin', '')}&nbsp;&nbsp;
            <i class="fab fa-github icon"></i>&nbsp;{data.get('github', '')}&nbsp;
            <hr class="black-line"> <!-- Black line here -->
        </p>
    """

    # Check if education fields are filled
    education_fields_filled = any(data.getlist(field) for field in ['institution[]', 'startingYear[]', 'endingYear[]', 'percentage[]'])
    if education_fields_filled:
        html_content += """
        <h2 class="section-title">Education</h2>
        <ul>
        """
        for i in range(len(data.getlist('institution[]'))):
            institution = data.getlist('institution[]')[i]
            starting_year = data.getlist('startingYear[]')[i]
            ending_year = data.getlist('endingYear[]')[i]
            percentage = data.getlist('percentage[]')[i]
            if institution.strip():
                html_content += f"<li>{institution} ({starting_year} - {ending_year}) - Percentage: {percentage}</li>\n"
        html_content += """
        </ul>
        """

    # Soft Skills
    if any(key.startswith('softskills') for key in data):
        html_content += """
        <h2 class="section-title">Soft Skills</h2>
        <ul>
        """
        for key, value in data.items():
            if key.startswith('softskills') and value.strip():
                html_content += f"<li>{value}</li>\n"
        html_content += """
        </ul>
        """

    # Technical Skills
    if any(key.startswith('technicalskills') for key in data):
        html_content += """
        <h2 class="section-title">Technical Skills</h2>
        <ul>
        """
        for key, value in data.items():
            if key.startswith('technicalskills') and value.strip():
                html_content += f"<li>{value}</li>\n"
        html_content += """
        </ul>
        """

    # Certifications
    if any(key.startswith('certifications') for key in data):
        html_content += """
        <h2 class="section-title">Certifications</h2>
        <ul>
        """
        for key, value in data.items():
            if key.startswith('certifications') and value.strip():
                html_content += f"<li>{value}</li>\n"
        html_content += """
        </ul>
        """

    # Languages Known
    if any(key.startswith('languages') for key in data):
        html_content += """
        <h2 class="section-title">Languages Known</h2>
        <ul>
        """
        for key, value in data.items():
            if key.startswith('languages') and value.strip():
                html_content += f"<li>{value}</li>\n"
        html_content += """
        </ul>
        """

    # Projects
    projects_fields_filled = any(data.getlist(field) for field in ['projectTitle[]', 'projectDescription[]', 'stackUsed[]'])
    if projects_fields_filled:
        html_content += """
        <h2 class="section-title">Projects</h2>
        <ul>
        """
        for i in range(len(data.getlist('projectTitle[]'))):
            title = data.getlist('projectTitle[]')[i]
            description = data.getlist('projectDescription[]')[i]
            stack = data.getlist('stackUsed[]')[i]
            if title.strip() or description.strip() or stack.strip():
                html_content += f"<li><strong>{title}:</strong><br>{description}<br><strong>Stack Used:</strong> {stack}</li>\n"
        html_content += """
        </ul>
        """

    # Internships
    internships_fields_filled = any(data.getlist(field) for field in ['companyName[]', 'role[]', 'duration[]'])
    if internships_fields_filled:
        html_content += """
        <h2 class="section-title">Internships</h2>
        <ul>
        """
        for i in range(len(data.getlist('companyName[]'))):
            company = data.getlist('companyName[]')[i]
            role = data.getlist('role[]')[i]
            duration = data.getlist('duration[]')[i]
            if company.strip() or role.strip() or duration.strip():
                html_content += f"<li>{company}<br><strong>Role: </strong>{role}<br><strong>Duration:</strong> {duration}</li>\n"
        html_content += """
        </ul>
        """

    # Interests
    if any(key.startswith('interests') for key in data):
        html_content += """
        <h2 class="section-title">Interests</h2>
        <ul>
        """
        for key, value in data.items():
            if key.startswith('interests') and value.strip():
                html_content += f"<li>{value}</li>\n"
        html_content += """
        </ul>
        """

    html_content += """
    </body>
    </html>
    """
    
    
    pdf_path = tempfile.mktemp(suffix='.pdf')

    # Convert HTML to PDF using xhtml2pdf
    with open(pdf_path, 'wb') as file:
        pisa.CreatePDF(html_content, dest=file)

    # Upload the PDF file to S3 bucket
    # try:
    #     with open(pdf_path, 'rb') as file:
    #         s3.upload_fileobj(file, S3_BUCKET_NAME, 'resume.pdf')
    #     return render_template('index.html', success_message='Form submitted successfully! Resume uploaded to S3.')
    # except Exception as e:
    #     return str(e), 500
    # finally:
    #     # Clean up: remove the temporary PDF file
    #     os.remove(pdf_path)
    
    with open('resume.html', 'w') as file:
        file.write(html_content)

    # Upload the HTML file to S3 bucket
    try:
        s3.upload_file('resume.html', S3_BUCKET_NAME, 'resume.html')
        return render_template('index.html', success_message='Form submitted successfully! Resume uploaded to S3.')
    except NoCredentialsError:
        return 'AWS credentials not available.'
    
@app.route('/download')
def download_resume():
    try:
        # Download file from S3
        temp_file_path = tempfile.mktemp(suffix='.html')
        s3.download_file(S3_BUCKET_NAME, 'resume.html', temp_file_path)
        return send_file(temp_file_path, as_attachment=True)
    except Exception as e:
        return str(e), 500

# Route for success page

if __name__ == '__main__':
    app.run(debug=True)
