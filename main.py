from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import time
import requests

base_url = 'https://example.com'
leaders_url = f'{base_url}/leaders'

images_dir = 'leader_images'
os.makedirs(images_dir, exist_ok=True)

# Configure Edge options
edge_options = Options()
edge_options.add_argument("--headless")  # Comment this out if you want to see the browser
edge_options.add_argument("--disable-gpu")

# Start Edge WebDriver
driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)

# Step 3: Open the page in Edge
driver.get(leaders_url)

# Wait for JavaScript to load the content
time.sleep(5)  # You can use WebDriverWait instead

# Step 4: Get the rendered page source
soup = BeautifulSoup(driver.page_source, 'html.parser')

driver.quit()

# Step 5: Find all leader cards
leader_cards = soup.find_all('div', class_='rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden transition-all hover:shadow-md')

print(f"Found {len(leader_cards)} leader cards.")

leaders_data = []

# Step 7: Extract data
for card in leader_cards:
    name_tag = card.find('h3', class_='whitespace-nowrap text-xl font-bold')
    name = name_tag.get_text(strip=True) if name_tag else 'Unknown'
    sanitized_name = re.sub(r'[\\/*?:"<>|]', "", name)

     # New extraction for approval rating and votes
    approval_section = card.find('div', class_='space-y-4')
    approval_rating = 'N/A'
    upvotes = 'N/A'
    total = 'N/A'

    if approval_section:
        approval_div = approval_section.find('div', class_='flex items-center justify-between mb-2')
        if approval_div:
            rating_span = approval_div.find_all('span', class_='font-bold')
            if rating_span:
                approval_rating = rating_span[0].get_text(strip=True)

        votes_div = approval_section.find('div', class_='flex justify-between items-center')
        if votes_div:
            upvote_div = votes_div.find_all('div', class_='text-center')[0]
            upvotes_value_div = upvote_div.find_all('div', class_='font-bold')
            if upvotes_value_div:
                upvotes = upvotes_value_div[0].get_text(strip=True)

            total_div = votes_div.find_all('div', class_='text-center')[1]
            total_value_div = total_div.find('div', class_='font-bold')
            if total_value_div:
                total = total_value_div.get_text(strip=True)

    img_tag = card.find('img')
    img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

    if img_url:

        try:
            if img_url.startswith('/'):
                img_url = base_url + img_url
            img_response = requests.get(img_url, verify=False)
            if img_response.status_code == 200:
                # Get extension from URL or response headers
                ext = os.path.splitext(img_url)[1]
                if not ext:
                    content_type = img_response.headers.get('Content-Type', '')
                    if 'jpeg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.img'
                image_path = os.path.join(images_dir, f"{sanitized_name}{ext}")
                with open(image_path, 'wb') as img_file:
                    img_file.write(img_response.content)
                image_filename = f"{sanitized_name}{ext}"
            else:
                image_filename = f"{sanitized_name}"
        except Exception as e:
            print(f"Error downloading image for {name}: {e}")
    else:
        print(f"No image URL found for {name}")

    leaders_data.append({'Name': name,'approval rate':approval_rating,'upvotes':upvotes,'total':total,'Image Filename': f"{sanitized_name}.jpg"})

# Save to CSV
csv_filename = 'leaders_data.csv'
pd.DataFrame(leaders_data).to_csv(csv_filename, index=False)

print(f"Data extraction complete. CSV saved as '{csv_filename}' and images saved in '{images_dir}' directory.")
