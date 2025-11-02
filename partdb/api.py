from typing import List, Dict, Any, Optional, Union

from .part import Part, Project

import json
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError
from urllib3.util.retry import Retry


class APIClient:
    """
    A robust API client for fetching data from JSON APIs using the requests library.
    """
    base_url:str
    timeout:int
    timeout: int
    retries: int

    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retries: int = 3
    ):
        """
        Initialize the API client with session management and retry logic.
        
        Args:
            base_url: The base URL of the API (e.g., 'https://api.example.com')
            default_headers: Optional default headers to include in all requests
            timeout: Default timeout for all requests in seconds
            retries: Number of retries for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Create a session with connection pooling and retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set default headers
        self.default_headers = default_headers or {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Python-API-Client/1.0'
        }
        self.session.headers.update(self.default_headers)
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build the complete URL.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Complete URL
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle the response and raise exceptions for HTTP errors.
        
        Args:
            response: The response object from requests
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            requests.exceptions.HTTPError: For HTTP errors
            requests.exceptions.JSONDecodeError: For invalid JSON responses
        """
        # Raise exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()
        
        # Return empty dict for no content responses
        if response.status_code == 204:
            return {}
        
        # Parse and return JSON response
        return response.json()
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a GET request.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            headers: Optional additional headers
            timeout: Optional request timeout in seconds
            **kwargs: Additional arguments to pass to requests.get()
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                **kwargs
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"GET request failed: {e}")
            raise
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a POST request.
        
        Args:
            endpoint: API endpoint path
            data: Form data to send in request body
            json_data: JSON data to send in request body
            params: Optional query parameters
            headers: Optional additional headers
            timeout: Optional request timeout in seconds
            **kwargs: Additional arguments to pass to requests.post()
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            response = self.session.post(
                url,
                data=data,
                json=json_data,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                **kwargs
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"POST request failed: {e}")
            raise
    
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Form data to send in request body
            json_data: JSON data to send in request body
            params: Optional query parameters
            headers: Optional additional headers
            timeout: Optional request timeout in seconds
            **kwargs: Additional arguments to pass to requests.put()
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            response = self.session.put(
                url,
                data=data,
                json=json_data,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                **kwargs
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"PUT request failed: {e}")
            raise
    
    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a PATCH request.
        
        Args:
            endpoint: API endpoint path
            data: Form data to send in request body
            json_data: JSON data to send in request body
            params: Optional query parameters
            headers: Optional additional headers
            timeout: Optional request timeout in seconds
            **kwargs: Additional arguments to pass to requests.patch()
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            response = self.session.patch(
                url,
                data=data,
                json=json_data,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                **kwargs
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"PATCH request failed: {e}")
            raise
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a DELETE request.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            headers: Optional additional headers
            timeout: Optional request timeout in seconds
            **kwargs: Additional arguments to pass to requests.delete()
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            response = self.session.delete(
                url,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.timeout,
                **kwargs
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"DELETE request failed: {e}")
            raise
    
    def _merge_headers(self, additional_headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        Merge additional headers with default headers.
        
        Args:
            additional_headers: Optional headers to merge
            
        Returns:
            Merged headers dictionary
        """
        if additional_headers:
            merged = self.default_headers.copy()
            merged.update(additional_headers)
            return merged
        return self.default_headers
    
    def close(self):
        """Close the session and release resources."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage with authentication
class AuthenticatedAPIClient(APIClient):
    """API client with built-in authentication support."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        auth_type: str = 'bearer'
    ):
        """
        Initialize authenticated API client.
        
        Args:
            base_url: The base URL of the API
            api_key: API key for authentication
            auth_type: Type of authentication ('bearer', 'basic', 'custom')
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if auth_type == 'bearer':
            headers['Authorization'] = f'Bearer {api_key}'
        elif auth_type == 'custom':
            headers['X-API-Key'] = api_key
        
        super().__init__(base_url, headers)


class PartDB:
    bearer:str
    base_url:str

    def __init__(self, bearer:str,base_url:str ) -> None:
        self.bearer = bearer
        self.base_url = base_url
        self.client = AuthenticatedAPIClient(
            base_url=self.base_url, 
            api_key=self.bearer
        )
        logging.debug(f'Initialized PartDB with {base_url=}')

    def get_part_from_id(self,id:str) -> Optional[Part]:
        try:
            data = self.client.get(f'parts/{id}')
            part = Part.from_dict(data)
            return part 
        except Exception as e :
            logging.exception('Error building Part instance from data')
            return None
        
    def list_projects(self):
        try:
            data = self.client.get('projects')
            projects = [Project.from_dict(proj_data) for proj_data in data["hydra:member"]]
            return projects
        except Exception as e :
            logging.exception('Error fetching projects')
            return []
    

    # def get_parts_from_mpn(self,mpn:str) -> List[Part]:
    #     req = Request(
    #             url = f"{self.base_url}/parts/?manufacturer_product_number={mpn}",
    #             )
    #     req.add_header("Authorization",f"Bearer {self.bearer}")
    #     resp:HTTPResponse = urlopen(req)
    #     data = resp_to_dict(resp)
    #     parts = [Part.from_dict(part) for part in data["hydra:member"]]
    #     return parts

