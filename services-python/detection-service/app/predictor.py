import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import base64
import io
import os

MODEL_PATH = os.getenv("MODEL_PATH", "models/resnet50_mammography.pt")
DEVICE = torch.device("cpu")
CLASSES = ["Cancer", "Non-Cancer"]

model = models.resnet50(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict(image_base64: str) -> dict:
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        conf, idx = torch.max(probs, 1)

    return {
        "prediction": CLASSES[idx.item()],
        "confidence": round(conf.item(), 4)
    }