import requests

def http(url, method, json=None):
    API_URL = "http://localhost:5000"

    if method not in ("GET", "POST", "PUT", "DELETE"):
        raise AttributeError(f"HTTP method {method} not supported.")
    
    func = getattr(requests, method.lower())
    return func(API_URL + url, json=json)

def main():
    response = http("/api/product/bananas", "GET")
    print(response.json())

if __name__ == "__main__":
    main()