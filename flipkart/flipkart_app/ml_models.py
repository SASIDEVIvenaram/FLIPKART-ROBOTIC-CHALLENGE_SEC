import torch
from PIL import Image
import torchvision.transforms as transforms

# Load each PyTorch model
# Modify the path to your actual saved model paths
object_detection_model = torch.load('flipkart/flipkart_app/ml_models/packed_and_unpacked.pt')
expiry_check_model = torch.load('flipkart/flipkart_app/ml_models/expmrp.pt')
freshness_check_model = torch.load('flipkart/flipkart_app/ml_models/fruit.pth')
#product_count_model = torch.load('path/to/product_count_model.pt')
#weight_verification_model = torch.load('path/to/weight_verification_model.pt')

# Set models to evaluation mode (if necessary)
object_detection_model.eval()
expiry_check_model.eval()
freshness_check_model.eval()
#product_count_model.eval()
#weight_verification_model.eval()

# Define transformations (this may vary depending on how your models were trained)
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
])

def run_ml_model(order):
    """
    This function runs all ML models on the given order to verify object detection, expiry, 
    freshness, product count, and weight.
    """
    # Placeholder for input data (replace with actual input data for each model)
    # For example, if you are passing images from the product, load the image files here
    product_image_path = order.product_image_path  # Replace with actual image path from the order
    product_weight = order.weight                  # Replace with actual weight value from the order

    # Load product image
    image = Image.open(product_image_path)
    image = transform(image)
    image = image.unsqueeze(0)  # Add batch dimension

    # Object Detection (Packing Status)
    with torch.no_grad():
        object_detection_output = object_detection_model(image)
        # Convert model output into a readable format (example output parsing)
        object_detection_result = 'Packed' if object_detection_output.argmax() == 1 else 'Unpacked'

    # Expiry Check
    with torch.no_grad():
        expiry_check_output = expiry_check_model(image)
        expiry_check_result = 'Valid' if expiry_check_output.argmax() == 1 else 'Expired'

    # Freshness Detection
    with torch.no_grad():
        freshness_check_output = freshness_check_model(image)
        freshness_check_result = 'Fresh' if freshness_check_output.argmax() == 1 else 'Not Fresh'

    # Product Count Verification (assuming you have an ML model for this)
    # with torch.no_grad():
    #     product_count_output = product_count_model(image)
    #     product_count_result = True if product_count_output.argmax() == 1 else False

    # # Weight Verification
    # # Assuming the weight verification model takes actual and expected weights as input
    # with torch.no_grad():
    #     weight_verification_input = torch.tensor([product_weight], dtype=torch.float32)
    #     weight_verification_output = weight_verification_model(weight_verification_input)
    #     weight_verification_result = True if weight_verification_output.argmax() == 1 else False

    # Compile all results into a single dictionary
    result = {
        'object_detection': object_detection_result,
        'expiry_check': expiry_check_result,
        'freshness_check': freshness_check_result,
        # 'product_count_check': product_count_result,
        # 'weight_verification': weight_verification_result
    }

    return result
