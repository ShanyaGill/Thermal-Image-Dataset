import json
import matplotlib.pyplot as plt
import numpy as np

# Load the JSON data from file
file_path = 'images.json'  # Update this to the path of your JSON file if different
with open(file_path, 'r') as file:
    data = json.loads(file.readline())

# Extract the temperature measurements
temperature_measurements = data['image']

# Convert the temperature measurements to a NumPy array for better handling
temperature_array = np.array(temperature_measurements)

# Display the thermal image
plt.imshow(temperature_array, cmap='inferno')  # 'inferno' is a good colormap for thermal data
plt.colorbar()  # Show a color bar indicating the temperature scale
plt.title('Thermal Image')
# Save the figure to a file
output_image_path = 'thermal_image.png'  # The path and filename where the image will be saved
plt.savefig(output_image_path, dpi=300)  # Save the figure as a PNG file with high resolution
plt.show()
