import requests
import sys
import json
from datetime import datetime

class GroceryAPITester:
    def __init__(self, base_url="https://campus-eats-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_order_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: {len(response_data)} items returned")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Test User {timestamp}",
            "address": "123 Campus Drive, Dorm Room 101",
            "phone": "555-0123"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/register",
            200,
            data=user_data
        )
        
        if success:
            self.user_data = user_data
            return True
        return False

    def test_login(self):
        """Test user login"""
        if not self.user_data:
            print("❌ Cannot test login - no user data available")
            return False
            
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token received: {self.token[:20]}...")
            return True
        return False

    def test_get_products(self):
        """Test getting all products"""
        success, response = self.run_test(
            "Get All Products",
            "GET",
            "api/products",
            200
        )
        return success and isinstance(response, list) and len(response) > 0

    def test_get_products_with_category(self):
        """Test getting products by category"""
        success, response = self.run_test(
            "Get Products by Category (fruits)",
            "GET",
            "api/products?category=fruits",
            200
        )
        return success and isinstance(response, list)

    def test_search_products(self):
        """Test product search"""
        success, response = self.run_test(
            "Search Products (banana)",
            "GET",
            "api/products?search=banana",
            200
        )
        return success and isinstance(response, list)

    def test_get_categories(self):
        """Test getting product categories"""
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "api/categories",
            200
        )
        return success and isinstance(response, list) and len(response) > 0

    def test_create_order(self):
        """Test creating an order"""
        if not self.token:
            print("❌ Cannot test order creation - not authenticated")
            return False
            
        # First get some products to order
        success, products = self.run_test(
            "Get Products for Order",
            "GET",
            "api/products",
            200
        )
        
        if not success or not products:
            print("❌ Cannot create order - no products available")
            return False
            
        # Create order with first two products
        order_items = [
            {"product_id": products[0]["id"], "quantity": 2},
            {"product_id": products[1]["id"], "quantity": 1}
        ]
        
        order_data = {
            "items": order_items,
            "delivery_address": "123 Campus Drive, Dorm Room 101"
        }
        
        success, response = self.run_test(
            "Create Order",
            "POST",
            "api/orders",
            200,
            data=order_data
        )
        
        if success and 'id' in response:
            self.created_order_id = response['id']
            print(f"   Order created with ID: {self.created_order_id}")
            return True
        return False

    def test_get_user_orders(self):
        """Test getting user's orders"""
        if not self.token:
            print("❌ Cannot test get orders - not authenticated")
            return False
            
        success, response = self.run_test(
            "Get User Orders",
            "GET",
            "api/orders",
            200
        )
        return success and isinstance(response, list)

    def test_mock_payment(self):
        """Test mock payment processing"""
        if not self.token or not self.created_order_id:
            print("❌ Cannot test payment - no order available")
            return False
            
        success, response = self.run_test(
            "Process Mock Payment",
            "POST",
            f"api/orders/{self.created_order_id}/pay",
            200
        )
        return success and 'message' in response

    def test_invalid_endpoints(self):
        """Test error handling for invalid endpoints"""
        success, response = self.run_test(
            "Invalid Endpoint (404)",
            "GET",
            "api/nonexistent",
            404
        )
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthorized Order Access",
            "GET",
            "api/orders",
            401
        )
        
        # Restore token
        self.token = temp_token
        return success

def main():
    print("🚀 Starting Grocery Delivery API Tests")
    print("=" * 50)
    
    tester = GroceryAPITester()
    
    # Test sequence
    test_results = []
    
    # Basic API tests (no auth required)
    test_results.append(("Get Products", tester.test_get_products()))
    test_results.append(("Get Categories", tester.test_get_categories()))
    test_results.append(("Get Products by Category", tester.test_get_products_with_category()))
    test_results.append(("Search Products", tester.test_search_products()))
    
    # Authentication tests
    test_results.append(("User Registration", tester.test_register()))
    test_results.append(("User Login", tester.test_login()))
    
    # Authenticated tests
    if tester.token:
        test_results.append(("Create Order", tester.test_create_order()))
        test_results.append(("Get User Orders", tester.test_get_user_orders()))
        test_results.append(("Mock Payment", tester.test_mock_payment()))
    
    # Error handling tests
    test_results.append(("Invalid Endpoint", tester.test_invalid_endpoints()))
    test_results.append(("Unauthorized Access", tester.test_unauthorized_access()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    print(f"API Tests: {tester.tests_passed}/{tester.tests_run} individual API calls passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the backend implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())