from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a gradient background
size = 64
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a circular background with gradient effect
for i in range(size//2):
    alpha = int(255 * (1 - i/(size//2)))
    color = (102, 126, 234, alpha)  # Purple gradient matching the app
    draw.ellipse([i, i, size-i, size-i], fill=color)

# Try to use a system font that supports emoji
try:
    # Windows emoji font
    font = ImageFont.truetype("seguiemj.ttf", 36)
except:
    try:
        # Fallback to Arial
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        # Use default font
        font = ImageFont.load_default()

# Draw the money bag emoji
emoji = "💰"
# Calculate text position to center it
bbox = draw.textbbox((0, 0), emoji, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (size - text_width) // 2 - bbox[0]
y = (size - text_height) // 2 - bbox[1]

try:
    draw.text((x, y), emoji, font=font, embedded_color=True)
except:
    # If embedded_color doesn't work, try without it
    draw.text((x, y), emoji, fill=(255, 215, 0), font=font)

# Save as ICO
output_path = os.path.join('static', 'favicon.ico')
img.save(output_path, format='ICO', sizes=[(32, 32), (16, 16)])

print(f"Favicon created at: {output_path}")
