import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# === Setup Chrome ===
options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === Ask user for profile code ===
profile_code = input("Enter Vinted profile code (the number in the profile URL): ").strip()
WARDROBE_URL = f"https://www.vinted.ro/member/{profile_code}"

def accept_cookies():
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
        )
        accept_btn.click()
        print("🍪 Cookies accepted")
    except:
        pass

def get_seller_name():
    driver.get(WARDROBE_URL)
    accept_cookies()
    time.sleep(3)
    try:
        seller_name_sel = "#content > div > div.container > div > div:nth-child(1) > div > div.u-flex-grow > div:nth-child(1) > div.web_ui__Cell__content > div.web_ui__Cell__heading > div > div > h1"
        seller_name = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, seller_name_sel))
        ).text.strip()
        print(f"👤 Seller name found: {seller_name}")
        return seller_name
    except Exception as e:
        print(f"⚠️ Could not find seller name: {e}")
        return "UnknownSeller"

def dismiss_login_popup():
    try:
        close_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div:nth-child(202) > div > div > div > div.web_ui__Navigation__navigation > div > div.web_ui__Navigation__right > button"))
        )
        close_btn.click()
        print("🔐 Dismissed login popup")
        time.sleep(1)
    except:
        pass

def extract_title():
    selectors = [
        "#sidebar > div.item-page-sidebar-content > div:nth-child(1) > div > div.web_ui__Cell__cell.web_ui__Cell__default > div > div > div > div.details-list.details-list--main-info > div:nth-child(1) > div:nth-child(1) > h1",
        "#sidebar > div.item-page-sidebar-content > div:nth-child(1) > div > div > div > div > div > div.details-list.details-list--main-info > div:nth-child(1) > div:nth-child(1) > h1"
    ]
    for sel in selectors:
        try:
            title = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
            if title:
                return title
        except:
            continue
    return ""

def extract_description():
    more_btn_selectors = [
        "#sidebar > div.item-page-sidebar-content > div:nth-child(1) > div > div.web_ui__Cell__cell.web_ui__Cell__default > div > div > div > div.details-list__info > div:nth-child(3) > div > div > div.u-text-wrap > button > span",
        "#sidebar > div.item-page-sidebar-content > div:nth-child(1) > div > div > div > div > div > div.details-list__info > div:nth-child(3) > div > div > div.u-text-wrap > button > span"
    ]
    for more_sel in more_btn_selectors:
        try:
            more_btn = driver.find_element(By.CSS_SELECTOR, more_sel)
            if more_btn.is_displayed():
                more_btn.click()
                time.sleep(0.5)
                break
        except:
            continue

    description_selectors = [
        "#sidebar > div.item-page-sidebar-content > div:nth-child(1) > div > div.web_ui__Cell__cell.web_ui__Cell__default > div > div > div > div.details-list__info > div:nth-child(3) > div > div > div.u-text-wrap > div > span",
        "#sidebar > div.item-page-sidebar-content > div:nth-child(1) > div > div > div > div > div > div.details-list__info > div:nth-child(3) > div > div > div.u-text-wrap > div > span"
    ]
    for desc_sel in description_selectors:
        try:
            desc = driver.find_element(By.CSS_SELECTOR, desc_sel).text.strip()
            if desc:
                return desc
        except:
            continue
    return ""

def extract_image_urls():
    urls = []

    # Variant 1: Desktop thumbnails gallery
    try:
        thumbnails = driver.find_elements(By.CSS_SELECTOR,
            "section.u-tablets-up-only.desktop-image-gallery-plugin div.desktop-image-gallery-plugin__thumbnails-container ul li.item-photo-thumbnail button div div img")
        if thumbnails:
            for thumb in thumbnails:
                src = thumb.get_attribute("src")
                if src and src not in urls:
                    urls.append(src)
            if urls:
                return urls
    except:
        pass

    # Variant 2: Up to 5 thumbnails, 5th opens carousel with all images
    try:
        thumbnails = driver.find_elements(By.CSS_SELECTOR,
            "section > div > figure.item-description.u-flexbox.item-photo > button > div > img")
        for thumb in thumbnails:
            src = thumb.get_attribute("src")
            if src and src not in urls:
                urls.append(src)

        try:
            show_more_btn = driver.find_element(By.CSS_SELECTOR,
                "section > div > figure.item-description.u-flexbox.item-photo.item-photo--5 > button > div > div")
            if show_more_btn.is_displayed():
                show_more_btn.click()
                time.sleep(1.5)

                carousel_imgs = driver.find_elements(By.CSS_SELECTOR,
                    "body > div.image-carousel > div > div > img.image-carousel__image")
                for img in carousel_imgs:
                    src = img.get_attribute("src")
                    if src and src not in urls:
                        urls.append(src)

                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR, "body > div.image-carousel > button.close-button")
                    close_btn.click()
                except:
                    pass
        except:
            pass

    except:
        pass

    return urls

def save_images(image_urls, folder):
    for i, url in enumerate(image_urls, start=1):
        try:
            img_data = requests.get(url).content
            with open(os.path.join(folder, f"{i}.jpg"), 'wb') as f:
                f.write(img_data)
            print(f"🖼️ Image {i} saved")
        except Exception as e:
            print(f"⚠️ Error downloading image {url}: {e}")

def scrape_item(item_url, index):
    print(f"\n--- Processing item #{index}: {item_url}")
    driver.get(item_url)
    time.sleep(3)
    dismiss_login_popup()

    title = extract_title()
    description = extract_description()
    images = extract_image_urls()

    folder_name = f"{index:02d} - {title}".replace("/", "_").replace("\\", "_")
    folder = os.path.join(main_folder, folder_name)
    os.makedirs(folder, exist_ok=True)

    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"Found {len(images)} images")

    with open(os.path.join(folder, "info.txt"), "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n\nDescription: {description}")

    save_images(images, folder)

    print(f"✅ Saved item #{index}: '{title}' ({len(images)} images)")

def get_item_links():
    driver.get(WARDROBE_URL)
    accept_cookies()
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    item_links = []
    try:
        anchors = driver.find_elements(By.CSS_SELECTOR, "div.feed-grid a")
        seen = set()
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/items/" in href and href not in seen:
                item_links.append(href)
                seen.add(href)
    except Exception as e:
        print(f"Error finding item links: {e}")

    return item_links

# === MAIN ===
print("🔄 Loading wardrobe...")

seller_name = get_seller_name()

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
main_folder = os.path.join(desktop_path, f"VintedWardrobe - {seller_name}")
os.makedirs(main_folder, exist_ok=True)

links = get_item_links()

if not links:
    print("❌ No items found.")
else:
    print(f"🧺 Found {len(links)} items.")
    for idx, link in enumerate(links, start=1):
        scrape_item(link, idx)

print("\n✅ DONE! Check your Desktop →", main_folder)
driver.quit()
