import base64
from PIL import Image
import io
import json

# Colle ICI tout le JSON complet retourné par curl
response = '''{"prediction_id":"ff4372ec-d263-461b-9a36-8cbe3a7ae586","filename":"Cancer_val_00005.jpg","mask_base64":"iVBORw0KGgoAAAANSUhEUgAAAOAAAADgCAAAAAA/RjU9AAAC9ElEQVR4nO2dwXbiMBAEW/v2/39ZewAcmSWJpRnbKr2unHKw3EUPsiEvUKrW5s/dAc7GgnT+3h3gG0rk4HZfKdNtMiG1jU3rJsGib86boydtiucKllrqM3IttfmtSbA/IPHk9RkhcckXB2O+nzrTbls/e5PZddR1YG6Or3UzG+wMudvsEmPsTpDXYH/E5sE9q780wbGAL8Pz9LLuZEYTltDRh0gRHE9YQkcfIWNEIwnPtVOC4OkJg0RHdGq/orDg1H6qigrO7RdvcHI/SaFNhqAXEGTojY8oxW9UEOM3KMjxGxME+a3/vuiIIKlAN/gBVIEDgiw/jyiebkHYhLpBPL2CtAl1g3gsSKdTELfHuEE8FqRjQTp9gryrhBvEY0E6FqTTJQi8SrhBPBakY0E6FqRjQToWpGNBOhakY0E6FqRjQToWpGNBOhakY0E6FqRjQToWpGNBOhakY0E6FqRjQToWpGNBOhakY0E6FqRjQToWpGNBMvHPVQNgQToWpGNBOhakY0E6FqRjwQbi/0d2CU73/TdHWLrB3s/ZxjXY+4oe16C0eIOSG9zhBiejSms3WKS1G5S0doOS3OAOWoPdm4wbnBE32OAGZ2TlBpe/k1n+XlTS2g1KcoM73OCMuMEGNzgjbrDBDc6I/wBKx4JcHlvGwoIPLEjHgi2sK/3jxmvhBr2LfoA1o5L8nS9vLN8giWcZ6wo+6RTkzagbpPKatV5B3Iwu2+ALC75Dm9H+BhmGW8qBEWUYvlj0OfhVwojg/BU2CZdssG1gSHDyCnfxxhqc3LBlcEQnNqz7bKPPwVkN63uwMpx0vvdnPqqMC85jWH+SCAjebVjLj2ZPIoLXGVZJKseM3ggJXmUYKiG6HV7iGAgZvlW75HoReBTDDc4+pwmC126nvXlTBC++YtQiHTZNErzjongseZqgrna8usHHapmLHb1X+ZlcwceSowdm+PzHCYLbyr//nHXuXYwLTnInS77p1GJBOhakY0E6FqRjQToWpGNBOhakY0E6FqRjQTr/ANS4hK88xLZ2AAAAAElFTkSuQmCC","tumor_area_px":17892,"tumor_area_pct":35.66,"width":224,"height":224,"timestamp":"2026-05-17T15:50:32.886092"}'''

data = json.loads(response)
b64  = data["mask_base64"]
img  = Image.open(io.BytesIO(base64.b64decode(b64)))
img.save("tumor_mask.png")
print("Sauvegardé : tumor_mask.png")