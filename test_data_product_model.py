from src.models.yaml_data_product_loader import DataProductModel

def test_with_none():
    try:
        print("Testing DataProductModel with None...")
        dp = DataProductModel(**None)
    except Exception as e:
        print("Error when using None:", e)

def test_with_valid():
    try:
        print("\nTesting DataProductModel with valid mapping...")
        dp = DataProductModel(
            data_product="Test Product",
            description="A test data product.",
            business_terms={},
            tables=[],
            relationships=[],
            kpis=[]
        )
        print("Success! DataProductModel:", dp)
    except Exception as e:
        print("Error with valid mapping:", e)

if __name__ == "__main__":
    test_with_none()
    test_with_valid()
