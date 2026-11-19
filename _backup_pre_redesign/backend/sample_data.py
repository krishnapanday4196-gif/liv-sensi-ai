import os
import numpy as np
import cv2

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_scans")

def generate_synthetic_samples():
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    
    # Base canvas size
    h, w = 512, 512

    # 1. NORMAL LIVER SCAN
    # Smooth homogeneous parenchyma, normal vascular structures
    normal_img = np.zeros((h, w), dtype=np.uint8)
    # Liver contour (curved lobe)
    cv2.ellipse(normal_img, (256, 256), (190, 140), -15, 0, 360, 110, -1)
    # Parenchymal texture (fine speckle)
    noise = np.random.normal(0, 12, (h, w)).astype(np.int16)
    normal_img = np.clip(normal_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    normal_img = cv2.GaussianBlur(normal_img, (3, 3), 0)
    # Normal portal vein branches (hypoechoic tubular branches)
    cv2.ellipse(normal_img, (230, 250), (60, 12), 35, 0, 360, 35, -1)
    cv2.ellipse(normal_img, (280, 260), (45, 9), -25, 0, 360, 35, -1)
    cv2.imwrite(os.path.join(SAMPLE_DIR, "sample_normal_liver.png"), normal_img)

    # 2. FATTY LIVER (HEPATIC STEATOSIS) SCAN
    # Diffusely hyperechoic (bright), deep acoustic beam attenuation
    fatty_img = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(fatty_img, (256, 256), (195, 145), -15, 0, 360, 185, -1)
    # Deep beam attenuation gradient (brighter top, darker bottom)
    gradient = np.tile(np.linspace(1.2, 0.4, h)[:, None], (1, w))
    fatty_img = np.clip(fatty_img * gradient, 0, 255).astype(np.uint8)
    # Speckle noise
    noise = np.random.normal(0, 18, (h, w)).astype(np.int16)
    fatty_img = np.clip(fatty_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    fatty_img = cv2.GaussianBlur(fatty_img, (5, 5), 0)
    cv2.imwrite(os.path.join(SAMPLE_DIR, "sample_fatty_liver.png"), fatty_img)

    # 3. LIVER CIRRHOSIS SCAN
    # Coarse, heterogeneous texture with irregular nodular surface
    cirrhosis_img = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(cirrhosis_img, (256, 256), (180, 130), -15, 0, 360, 120, -1)
    # Add nodular irregularities to contour
    for angle in range(0, 360, 15):
        rad = np.radians(angle)
        nx = int(256 + (180 + np.random.randint(-15, 15)) * np.cos(rad))
        ny = int(256 + (130 + np.random.randint(-15, 15)) * np.sin(rad))
        cv2.circle(cirrhosis_img, (nx, ny), 18, np.random.randint(90, 150), -1)
    # Coarse heterogeneous speckle
    coarse = np.random.normal(0, 35, (h, w)).astype(np.int16)
    cirrhosis_img = np.clip(cirrhosis_img.astype(np.int16) + coarse, 0, 255).astype(np.uint8)
    cirrhosis_img = cv2.medianBlur(cirrhosis_img, 5)
    cv2.imwrite(os.path.join(SAMPLE_DIR, "sample_cirrhosis_liver.png"), cirrhosis_img)

    # 4. LIVER TUMOR / HCC SCAN
    # Distinct focal lesion / mass with peripheral rim enhancement
    tumor_img = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(tumor_img, (256, 256), (190, 140), -15, 0, 360, 110, -1)
    noise = np.random.normal(0, 14, (h, w)).astype(np.int16)
    tumor_img = np.clip(tumor_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    tumor_img = cv2.GaussianBlur(tumor_img, (3, 3), 0)
    # Focal lesion in right lobe (center ~ 300, 220)
    # Peripheral hypervascular ring
    cv2.circle(tumor_img, (310, 230), 45, 190, 8)
    # Heterogeneous internal necrotic core
    cv2.circle(tumor_img, (310, 230), 38, 65, -1)
    # Internal microvascular dots
    for _ in range(12):
        rx = 310 + np.random.randint(-20, 20)
        ry = 230 + np.random.randint(-20, 20)
        cv2.circle(tumor_img, (rx, ry), 2, 210, -1)
    cv2.imwrite(os.path.join(SAMPLE_DIR, "sample_liver_tumor.png"), tumor_img)

if __name__ == "__main__":
    generate_synthetic_samples()
    print("Sample medical scans generated successfully in:", SAMPLE_DIR)
