import os
import platform
import tempfile

from anomalous_vertices_detection.utils.label_encoder import BinaryLabelEncoder

graph_max_edge_number = 10000000
label_encoder = BinaryLabelEncoder()
save_progress_interval = 200000
temp_path = os.path.join(tempfile.gettempdir(), "temp_features.csv")
if platform.system() == 'Windows':
    pass
else:
    pass
