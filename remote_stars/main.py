import numpy as np
import socket
from skimage.measure import label
from scipy import ndimage

HOST = "84.237.21.36"
PORT = 5152
BUFFER_SIZE = 40002

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    client_socket.send(b"124ras1")
    print(client_socket.recv(10))
    
    status = b'nope'
    
    while status == b'nope':
        client_socket.send(b'get')
        
        result = bytearray()
        while len(result) < BUFFER_SIZE:
            chunk = client_socket.recv(BUFFER_SIZE - len(result))
            if not chunk:
                break
            result.extend(chunk)
        raw_data = result
        
        height, width = raw_data[0], raw_data[1]
        pixel_data = np.frombuffer(raw_data[2:BUFFER_SIZE], dtype="uint8")
        image = pixel_data.reshape(height, width)
        
        binary_mask = image > 0
        labeled_image = label(binary_mask)
        
        unique_labels = [1, 2]
        centers = []
        
        for lbl in unique_labels:
            if lbl not in labeled_image:
                distance = 0.0
                break
            region = labeled_image == lbl
            center = ndimage.center_of_mass(region)
            centers.append(center)
        else:
            x1, y1 = centers[0]
            x2, y2 = centers[1]
            distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        
        client_socket.send(str(round(distance, 1)).encode())
        print(client_socket.recv(10))
        
        client_socket.send(b'beat')
        status = client_socket.recv(10)
