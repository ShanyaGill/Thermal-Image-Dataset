import os
import re
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
import base64
from openai import OpenAI

client = OpenAI()
# Path to the JSON file containing all images
file_path = 'party_images1.json'

def read_new_image():
    """
    Generator function to yield one image data at a time from the file.
    """
    with open(file_path, 'r') as file:
        for line in file:
            yield json.loads(line)

def encode_image(image_path):
    """
    Encodes an image to a base64 string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image(image_path):
    """
    Sends the image to the API for analysis. The response includes information about the scene with a focus on humans and a boolean indicating the presence of humans.
    """
    encoded_string = encode_image(image_path)

    user_prompt = """
     Do the following analysis for the image and return the following JSON:
     {
        "presence of figures that look like a homo sapien or their body parts in the series of the images": <bool>,
        "description of what you see (arms, legs, face, torso, etc.)": <str>,
        "description of the overall temperature range and if there is any chance of a fire": <str>,
        "summary of above key points in array format within square brackets": [...]
      }
    """
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_string}",
                    },
                },
            ],
            }
        ],
        max_tokens=300,
    )

    # Extracting and formatting the response
    full_response_content = response.choices[0].message.content
    print("full_response_content:", full_response_content)
    try:
        analysis_result_match = re.search(r"```json(.+?)```", full_response_content, re.DOTALL)
        analysis_result = analysis_result_match.group(1) if analysis_result_match else "{}"
        analysis_items = json.loads(analysis_result)
    
        return [f"{v}" for v in list(analysis_items.values())[-1][1:]]
    except:
        return []

# Initialize the generator
image_generator = read_new_image()

# The size of the window (19 old images + 1 new image)
window_size = 10

# Initialize a list to hold the current window of images
image_window = []

# Directory where the collages will be saved
collage_directory = 'collages'
# Ensure the directory exists
os.makedirs(collage_directory, exist_ok=True)

# Initially fill the window with the first 10 images
for _ in range(window_size):
    try:
        next(image_generator)
        next(image_generator)
        next(image_generator)
        new_image_data = next(image_generator)
        image_window.append(new_image_data)
    except StopIteration:
        # This exception will be raised if there are no more images in the generator (end of file)
        break
# Initialize the figure and axes outside the loop, adjusting layout for latest image and analysis under the collage
fig = plt.figure(figsize=(13, 5))  # Adjusted figure size for better layout
gs = fig.add_gridspec(3, window_size, wspace=0.4, hspace=0.4)  # Adjusted grid spec for 3 rows, window_size columns, and added spacing
axs_collage = [fig.add_subplot(gs[0, i]) for i in range(window_size)]  # Collage subplots in the first row
for ax in axs_collage:
    ax.axis('off')
axs_latest = fig.add_subplot(gs[1:4, 0:3])  # Latest image subplot in the second row, spanning first 5 columns
axs_latest.axis('off')
axs_analysis = fig.add_subplot(gs[1:2, 3:8])  # Analysis subplot in the second row, spanning the remaining columns
# axs_analysis.axis('off')
collage_counter = 0
# Assuming this is inside a loop where you update image_window and other variables
while True:
    # Clear previous images and texts
    axs_latest.clear()
    axs_analysis.clear()
    axs_analysis.axis('off')  # You need to turn off the axis again after clearing

    # Your code to update image_window and other logic here
    try:
        next(image_generator)
        next(image_generator)
        next(image_generator)
        new_image_data = next(image_generator)
        # Replace the oldest image with the new one
        image_window.pop(0)  # Remove the oldest image
        image_window.append(new_image_data)  # Add the new image
    except StopIteration:
        # No more images to read; break the loop
        break

    # Initialize a variable to track if fire is detected in any image
    fire_detected_in_any_image = False
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    # Display each image in the collage
    for i, data in enumerate(image_window):
        temperature_measurements = data['image']
        temperature_array = np.array(temperature_measurements)

        # Check if there's fire (temperature > 60 degrees)
        is_fire = np.any(temperature_array > 60)
        if is_fire:
            axs_collage[i].set_title('Fire detected!', fontsize=12, color='red')  # Increased font size for larger subplot
            fire_detected_in_any_image = True  # Update the fire detection flag

        im_collage = axs_collage[i].imshow(temperature_array, cmap='inferno')

        # Clear previous thermal bar if exists
        if hasattr(axs_collage[i], 'cax'):
            axs_collage[i].cax.remove()

        # Add a thermal bar at the bottom of each picture in the collage, making it shorter
        divider = make_axes_locatable(axs_collage[i])
        cax = divider.append_axes("bottom", size="17%", pad=0.15)  # Reduced size to make the colorbar shorter
        axs_collage[i].cax = cax  # Store reference to cax for removal in next iteration
        colorbar = plt.colorbar(im_collage, cax=cax, orientation='horizontal')
        colorbar.set_ticks([int(temperature_array.min()), int(temperature_array.max())])  # Only show min and max temperature ticks as whole numbers
        colorbar.ax.tick_params(labelsize='x-small')  # Make the font size even smaller for improved readability
    
    # Save the collage array to a file
    collage_counter += 1
    collage_image_path = os.path.join(collage_directory, f'collage_{collage_counter}.png')
    # Create a new figure for the collage to avoid interference with the main figure
    fig_collage, axs_collage_save = plt.subplots(len(image_window), 1, figsize=(7, len(image_window) * 5))
    fig_collage.subplots_adjust(hspace=0.5)
    for idx, data in enumerate(image_window):
        temperature_measurements = data['image']
        temperature_array = np.array(temperature_measurements)
        axs_collage_save[idx].imshow(temperature_array, cmap='inferno')
        axs_collage_save[idx].axis('off')  # Optionally, turn off the axis for a cleaner look
    plt.savefig(collage_image_path, dpi=300, bbox_inches='tight')  # Save the collage as a PNG file with high resolution
    plt.close(fig_collage)  # Close the figure to free up memory

    # Clear previous image and thermal bar if exists
    axs_latest.clear()
    if hasattr(axs_latest, 'cax_latest'):
        axs_latest.cax_latest.remove()

    # Plot the latest image
    latest_temperature_measurements = image_window[-1]['image']
    latest_temperature_array = np.array(latest_temperature_measurements)
    im_latest = axs_latest.imshow(latest_temperature_array, cmap='inferno')
    axs_latest.axis('off')  # Optionally, turn off the axis for a cleaner look

    # Add a thermal bar for the latest picture
    divider_latest = make_axes_locatable(axs_latest)
    cax_latest = divider_latest.append_axes("bottom", size="5%", pad=0.35)
    axs_latest.cax_latest = cax_latest  # Store reference to cax_latest for removal in next iteration
    colorbar_latest = plt.colorbar(im_latest, cax=cax_latest, orientation='horizontal')
    colorbar_latest.ax.tick_params(labelsize='small')

    # Save the figure in the specified subdirectory with a unique name
    output_image_path = os.path.join(collage_directory, f'thermal_image_window_{collage_counter}.png')
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')  # Save the figure as a PNG file with high resolution and ensure all content fits
    analysis_text_list = analyze_image(output_image_path)  # Get the analysis result as a list

    # Format the analysis text list into a wrapped text with fixed width for better readability, adding more line spacing for clarity
    analysis_text = "Analysis:\n\n" + "\n\n".join([f"• {item}" for item in analysis_text_list])
    axs_analysis.text(0.0, 0.0, analysis_text, wrap=True, horizontalalignment='left', verticalalignment='center', transform=axs_analysis.transAxes, fontsize=12, color='red', bbox=dict(facecolor='#FFFF99', alpha=0.5, boxstyle="round,pad=0.5"), fontweight='bold', linespacing=1.5)
    # Redraw the figure with the updated data
    fig.canvas.draw_idle()
    # Display the updated figure
    plt.pause(1)  # Adjust the pause time as needed

# After the loop, you might want to keep the window open
plt.show()
